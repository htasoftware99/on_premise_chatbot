import streamlit as st
import requests
import uuid
from streamlit_mic_recorder import mic_recorder

# FastAPI Backend URL
API_URL = "http://localhost:8000"

# Sayfa Ayarları
st.set_page_config(
    page_title="Bilge AI Asistanı", 
    layout="wide", 
    page_icon="✨"
)

# --- CSS: BUTON VE SIDEBAR DÜZENİ ---
st.markdown("""
<style>
    .stButton button {
        border-radius: 20px;
    }
    /* Sidebar butonlarını biraz daha özelleştirelim */
    [data-testid="stSidebar"] button {
        width: 100%;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION YÖNETİMİ ---

# 1. Tüm sohbetleri tutacak liste
if "chat_sessions" not in st.session_state:
    # İlk varsayılan boş sohbet
    first_id = str(uuid.uuid4())
    st.session_state.chat_sessions = {
        first_id: {"title": "Yeni Sohbet", "messages": []}
    }
    st.session_state.active_session_id = first_id

# Yeni sohbet oluşturma fonksiyonu
def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chat_sessions[new_id] = {"title": "Yeni Sohbet", "messages": []}
    st.session_state.active_session_id = new_id

# Aktif sohbeti değiştirme fonksiyonu
def switch_chat(session_id):
    st.session_state.active_session_id = session_id

# Sohbet silme fonksiyonu (Tekil)
def delete_chat(session_id):
    if len(st.session_state.chat_sessions) > 1:
        del st.session_state.chat_sessions[session_id]
        # Eğer silinen aktif ise, rastgele birine geç
        if st.session_state.active_session_id == session_id:
            st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]
    else:
        # Tek sohbet varsa sadece içeriğini temizle
        st.session_state.chat_sessions[session_id]["messages"] = []
        st.session_state.chat_sessions[session_id]["title"] = "Yeni Sohbet"

# Aktif sohbet verilerini al
active_id = st.session_state.active_session_id
current_messages = st.session_state.chat_sessions[active_id]["messages"]

# --- SIDEBAR (SOL MENÜ) ---
with st.sidebar:
    st.title("🗂️ Geçmiş")
    
    if st.button("➕ Yeni Sohbet Oluştur", use_container_width=True):
        create_new_chat()
        st.rerun()
    
    st.divider()
    
    # Sohbetleri listele (Ters sırayla, en yeni en üstte)
    # Dictionary sırasızdır ama Python 3.7+ ekleme sırasını korur. Yine de ters çevirelim.
    session_ids = list(st.session_state.chat_sessions.keys())[::-1]
    
    for sess_id in session_ids:
        sess_data = st.session_state.chat_sessions[sess_id]
        title = sess_data["title"]
        
        # Aktif olanı vurgulamak için emoji koyalım
        if sess_id == active_id:
            label = f"🟢 {title}"
        else:
            label = f"⚫ {title}"
            
        col_btn, col_del = st.columns([0.85, 0.15])
        with col_btn:
            if st.button(label, key=f"btn_{sess_id}"):
                switch_chat(sess_id)
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{sess_id}", help="Bu sohbeti sil"):
                delete_chat(sess_id)
                st.rerun()

# --- ANA EKRAN ---

# Başlık
st.title("✨ Bilge AI Asistanı")
st.caption("Genel Sohbet | Web Arama | Döküman Analizi | 🎙️ Sesli Sohbet")

# --- DOSYA YÜKLEME ALANI ---
with st.expander("📎 Döküman Ekle (RAG için)", expanded=False):
    uploaded_file = st.file_uploader(
        "PDF, TXT veya MD dosyanı buraya sürükle bırak", 
        type=["txt", "md", "pdf"], 
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            with st.spinner("Dosya işleniyor..."):
                files = {"file": (uploaded_file.name, uploaded_file, "text/plain")}
                try:
                    res = requests.post(f"{API_URL}/upload", files=files)
                    if res.status_code == 200:
                        st.success(f"✅ {uploaded_file.name} başarıyla sisteme eklendi.")
                        st.session_state.last_uploaded = uploaded_file.name 
                    else:
                        st.error("❌ Yükleme başarısız.")
                except Exception as e:
                    st.error(f"Hata: {e}")

# --- CHAT GEÇMİŞİNİ GÖSTER (Aktif Session) ---
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- GİRİŞ ALANI YÖNETİMİ ---

final_prompt = None

# Layout düzeni için container
bottom_container = st.container()

with bottom_container:
    # Mikrofon ve uyarı alanları
    mic_col1, mic_col2 = st.columns([0.9, 0.1])
    
    with mic_col2:
        audio_data = mic_recorder(
            start_prompt="🎙️", 
            stop_prompt="⏹️", 
            just_once=True,
            key="mic_recorder",
            format="wav"
        )

# 1. Ses Kaydı
if audio_data is not None:
    audio_bytes = audio_data['bytes']
    with st.spinner("Ses metne çevriliyor..."):
        try:
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            res = requests.post(f"{API_URL}/transcribe", files=files)
            if res.status_code == 200:
                transcribed_text = res.json()["text"]
                if transcribed_text:
                    final_prompt = transcribed_text
            else:
                st.error("Ses işlenirken hata oluştu.")
        except Exception as e:
            st.error(f"Bağlantı hatası: {e}")

# 2. Yazılı Giriş
prompt = st.chat_input("Bir soru sorun...")

if prompt and not final_prompt:
    final_prompt = prompt

# --- SOHBET AKIŞI VE KAYIT ---
if final_prompt:
    # 1. Kullanıcı mesajını ekle (Aktif Session'a)
    st.session_state.chat_sessions[active_id]["messages"].append({"role": "user", "content": final_prompt})
    
    # 2. Eğer bu "Yeni Sohbet" ise başlığını güncelle (İlk 30 karakter)
    if st.session_state.chat_sessions[active_id]["title"] == "Yeni Sohbet":
        new_title = final_prompt[:30] + "..." if len(final_prompt) > 30 else final_prompt
        st.session_state.chat_sessions[active_id]["title"] = new_title

    # Ekrana yazdır
    with st.chat_message("user"):
        st.markdown(final_prompt)

    # Asistan cevabını bekle
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            response = requests.post(f"{API_URL}/chat", json={"query": final_prompt})
            
            if response.status_code == 200:
                data = response.json()
                answer = data["response"]
                intent = data["intent"]
                source = data["source"]
                
                intent_map = {
                    "web_search_query": "🌐 Web",
                    "document_qa": "📄 Döküman",
                    "general_chat": "💬 Sohbet"
                }
                badge = intent_map.get(intent, intent)

                full_response = f"{answer}\n\n---\n*Kaynak: `{source}` ({badge})*"
                message_placeholder.markdown(full_response)
                
                # 3. Asistan cevabını kaydet (Aktif Session'a)
                st.session_state.chat_sessions[active_id]["messages"].append({"role": "assistant", "content": full_response})
                
                # Sidebar'daki başlığın güncellenmesi için sayfayı yenile (Opsiyonel ama iyi görünür)
                st.rerun()
                
            else:
                message_placeholder.markdown("❌ Sunucu hatası.")
        except Exception as e:
            message_placeholder.markdown(f"❌ Bağlantı hatası: {e}")