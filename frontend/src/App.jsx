import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Mic, Send, Paperclip, Plus, Trash2, StopCircle, MessageSquare, FileText, X } from 'lucide-react';
import './App.css';

const API_URL = "http://localhost:8000";

// Basit bir ID oluşturucu
const generateId = () => Math.random().toString(36).substr(2, 9);

function App() {
  // --- STATE YÖNETİMİ ---
  
  // Tüm sohbet oturumlarını tutan ana state
  const [sessions, setSessions] = useState([
    { id: '1', title: 'Yeni Sohbet', messages: [], file: null }
  ]);
  
  // Hangi sohbetin açık olduğunu tutan state
  const [activeSessionId, setActiveSessionId] = useState('1');
  
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);

  // Aktif sohbeti bulma yardımcısı
  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  
  // Otomatik scroll
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(scrollToBottom, [activeSession.messages]);

  // --- YENİ SOHBET / SOHBET DEĞİŞTİRME ---

  const createNewChat = async () => {
    // 1. Backend'i sıfırla
    try {
        await axios.post(`${API_URL}/reset`);
    } catch (err) {
        console.error("Resetleme hatası:", err);
    }

    // 2. Frontend'de yeni sayfa aç
    const newId = generateId();
    const newSession = { id: newId, title: 'Yeni Sohbet', messages: [], file: null };
    setSessions(prev => [newSession, ...prev]); 
    setActiveSessionId(newId);
  };

  const switchSession = (id) => {
    setActiveSessionId(id);
  };

  const deleteSession = (e, id) => {
    e.stopPropagation(); // Butona basınca sohbeti açmasını engelle
    const filtered = sessions.filter(s => s.id !== id);
    setSessions(filtered);
    
    // Eğer sildiğimiz aktifse, ilkini veya yeni bir tane aç
    if (activeSessionId === id) {
        if (filtered.length > 0) setActiveSessionId(filtered[0].id);
        else createNewChat();
    }
  };

  // --- MESAJ GÖNDERME ---

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    
    // 1. Kullanıcı mesajını ekle
    updateCurrentSessionMessages(userMsg);
    
    // 2. Eğer bu ilk mesajsa, sohbet başlığını güncelle
    if (activeSession.messages.length === 0) {
        updateSessionTitle(activeSessionId, input);
    }

    setInput("");
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, { query: userMsg.content });
      const aiMsg = { 
        role: "assistant", 
        content: res.data.response,
        source: res.data.source,
        intent: res.data.intent
      };
      updateCurrentSessionMessages(aiMsg);
    } catch (error) {
      console.error("Hata:", error);
      updateCurrentSessionMessages({ role: "assistant", content: "⚠️ Bir hata oluştu." });
    } finally {
      setIsLoading(false);
    }
  };

  // State güncelleme yardımcıları
  const updateCurrentSessionMessages = (msg) => {
    setSessions(prev => prev.map(session => 
        session.id === activeSessionId 
        ? { ...session, messages: [...session.messages, msg] }
        : session
    ));
  };

  const updateSessionTitle = (id, text) => {
      const newTitle = text.length > 25 ? text.substring(0, 25) + "..." : text;
      setSessions(prev => prev.map(session => 
        session.id === id ? { ...session, title: newTitle } : session
      ));
  };

  // --- DOSYA YÖNETİMİ ---

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      await axios.post(`${API_URL}/upload`, formData);
      
      setSessions(prev => prev.map(session => 
        session.id === activeSessionId 
        ? { ...session, file: selectedFile.name }
        : session
      ));
      
      alert("Dosya başarıyla yüklendi ve işlendi.");
    } catch (error) {
      alert("Dosya yüklenemedi.");
    } finally {
      // KRİTİK NOKTA: Input değerini sıfırla ki aynı dosya tekrar seçilebilsin
      e.target.value = ""; 
    }
  };
  const removeFile = () => {
      setSessions(prev => prev.map(session => 
        session.id === activeSessionId 
        ? { ...session, file: null }
        : session
      ));
      
  };

  // --- SES KAYDI ---
  
  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        audioChunksRef.current = [];
        mediaRecorderRef.current.ondataavailable = (e) => audioChunksRef.current.push(e.data);
        mediaRecorderRef.current.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const formData = new FormData();
          formData.append("file", audioBlob, "recording.wav");
          setIsLoading(true);
          try {
            const res = await axios.post(`${API_URL}/transcribe`, formData);
            setInput(res.data.text);
          } catch { alert("Ses çevrilemedi."); } 
          finally { setIsLoading(false); }
        };
        mediaRecorderRef.current.start();
        setIsRecording(true);
      } catch { alert("Mikrofon izni gerekli!"); }
    }
  };

  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        <button className="new-chat-btn" onClick={createNewChat}>
          <Plus size={20} /> Yeni Sohbet
        </button>
        
        <div className="history-label">GEÇMİŞ SOHBETLER</div>
        
        <div className="chat-list">
            {sessions.map(session => (
                <div 
                    key={session.id} 
                    onClick={() => switchSession(session.id)}
                    className={`chat-item ${session.id === activeSessionId ? 'active' : ''}`}
                >
                    <MessageSquare size={16} />
                    <span className="chat-title">{session.title}</span>
                    <button className="delete-chat-btn" onClick={(e) => deleteSession(e, session.id)}>
                        <Trash2 size={14} />
                    </button>
                </div>
            ))}
        </div>
      </div>

      {/* MAIN CHAT */}
      <div className="chat-area">
        <div className="messages-container">
          {activeSession.messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✨</div>
              <h1>Merhaba, Hasan</h1>
              <p>RAG destekli asistanın hazır.</p>
            </div>
          ) : (
            activeSession.messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role === 'user' ? 'user-msg' : 'ai-msg'}`}>
                <ReactMarkdown>{msg.content}</ReactMarkdown>
                {msg.source && <span className="source-badge">{msg.source}</span>}
              </div>
            ))
          )}
          {isLoading && <div className="message ai-msg">Thinking...</div>}
          <div ref={messagesEndRef} />
        </div>

        {/* INPUT AREA */}
        <div className="input-area">
            {/* Yüklenen Dosya Göstergesi (Input'un hemen üstünde) */}
            {activeSession.file && (
                <div className="file-preview-badge">
                    <FileText size={16} color="#6366f1" />
                    <span>{activeSession.file}</span>
                    <button onClick={removeFile}><X size={14} /></button>
                </div>
            )}

          <div className="input-wrapper">
            <input type="file" id="file-upload" style={{display: 'none'}} onChange={handleFileUpload} />
            
            <button className="icon-btn" onClick={() => document.getElementById('file-upload').click()}>
              <Paperclip size={20} />
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Bir şeyler yazın..."
              rows={1}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
            />

            <button className={`icon-btn ${isRecording ? 'recording' : ''}`} onClick={toggleRecording}>
              {isRecording ? <StopCircle size={20} /> : <Mic size={20} />}
            </button>

            <button className="icon-btn send-btn" onClick={sendMessage}>
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;