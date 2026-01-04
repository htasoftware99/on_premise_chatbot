# import streamlit as st
# import requests

# # FastAPI Backend URL
# API_URL = "http://localhost:8000"

# # Sayfa Ayarları (Sidebar kapalı, başlık sade)
# st.set_page_config(
#     page_title="Gemma AI", 
#     layout="centered", # Sohbet deneyimi için 'centered' daha odaklıdır, istersen 'wide' yapabilirsin
#     page_icon="🤖"
# )

# # --- BAŞLIK ALANI (HEADER) ---
# col1, col2 = st.columns([0.85, 0.15])

# with col1:
#     st.title("🤖 AI Asistanı")
#     st.caption("Genel Sohbet | Web Arama | Döküman Analizi")

# with col2:
#     # Sohbeti Temizle Butonu (Sağ üst köşede)
#     if st.button("🗑️ Temizle", help="Sohbet geçmişini siler"):
#         st.session_state.messages = []
#         st.rerun()

# # --- DOSYA YÜKLEME ALANI (ANA EKRAN) ---
# # Sidebar yerine, sohbetin hemen üzerinde gizlenip açılabilen bir alan
# with st.expander("📎 Döküman Ekle (RAG için buraya sürükle)", expanded=False):
#     uploaded_file = st.file_uploader(
#     "PDF, TXT veya MD dosyanı buraya sürükle bırak", 
#     type=["txt", "md", "pdf"], # PDF eklendi
#     label_visibility="collapsed"
# )
    
#     # Dosya yüklendiği anda backend'e gönder
#     if uploaded_file is not None:
#         # Dosya daha önce yüklenmediyse işlemi başlat (session state kontrolü)
#         if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
#             with st.spinner("Dosya işleniyor..."):
#                 files = {"file": (uploaded_file.name, uploaded_file, "text/plain")}
#                 try:
#                     res = requests.post(f"{API_URL}/upload", files=files)
#                     if res.status_code == 200:
#                         st.success(f"✅ {uploaded_file.name} başarıyla sisteme eklendi.")
#                         st.session_state.last_uploaded = uploaded_file.name # Tekrar yüklemeyi önle
#                     else:
#                         st.error("❌ Yükleme başarısız.")
#                 except Exception as e:
#                     st.error(f"Hata: {e}")

# # --- CHAT GEÇMİŞİ ---
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Mesajları göster
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # --- INPUT ALANI ---
# if prompt := st.chat_input("Bir soru sorun (örn: Bu rapor ne anlatıyor? Dolar ne kadar? Merhaba)..."):
    
#     # Kullanıcı mesajı
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Asistan cevabı
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         message_placeholder.markdown("Thinking...")
        
#         try:
#             response = requests.post(f"{API_URL}/chat", json={"query": prompt})
            
#             if response.status_code == 200:
#                 data = response.json()
#                 answer = data["response"]
#                 intent = data["intent"]
#                 source = data["source"]
                
#                 # Intent Rozetleri (Sadeleştirilmiş)
#                 intent_map = {
#                     "web_search_query": "🌐 Web",
#                     "document_qa": "📄 Döküman",
#                     "general_chat": "💬 Sohbet"
#                 }
#                 badge = intent_map.get(intent, intent)

#                 # Cevabı göster
#                 full_response = f"{answer}\n\n---\n*Kaynak: `{source}` ({badge})*"
#                 message_placeholder.markdown(full_response)
                
#                 # Geçmişe ekle
#                 st.session_state.messages.append({"role": "assistant", "content": full_response})
#             else:
#                 message_placeholder.markdown("❌ Sunucu hatası.")
#         except Exception as e:
#             message_placeholder.markdown(f"❌ Bağlantı hatası: {e}")



import streamlit as st
import requests

# FastAPI Backend URL
API_URL = "http://localhost:8000"

# Sayfa Ayarları
st.set_page_config(
    page_title="Gemma AI", 
    layout="centered",
    page_icon="🤖"
)

# --- BAŞLIK ALANI ---
col1, col2 = st.columns([0.85, 0.15])

with col1:
    st.title("🤖 AI Asistanı")
    st.caption("Genel Sohbet | Web Arama | Döküman Analizi | 🎙️ Sesli Sohbet")

with col2:
    if st.button("🗑️ Temizle", help="Sohbet geçmişini siler"):
        st.session_state.messages = []
        st.rerun()

# --- DOSYA YÜKLEME ALANI ---
with st.expander("📎 Döküman Ekle (RAG için buraya sürükle)", expanded=False):
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

# --- CHAT GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INPUT ALANI YÖNETİMİ ---

# Kullanıcı metin girmek isterse
prompt = st.chat_input("Bir soru sorun...")

# Kullanıcı ses kaydı yapmak isterse (Metin girişiyle aynı hizada dursun diye altına ekledik)
audio_value = st.audio_input("Veya sesli sorun 🎙️")

final_prompt = None

# 1. Durum: Sesli Giriş Var mı?
if audio_value:
    with st.spinner("Ses metne çevriliyor..."):
        try:
            # Sesi backend'e gönder
            files = {"file": ("audio.wav", audio_value, "audio/wav")}
            res = requests.post(f"{API_URL}/transcribe", files=files)
            
            if res.status_code == 200:
                transcribed_text = res.json()["text"]
                final_prompt = transcribed_text # Ses metne döndü, prompt olarak ata
            else:
                st.error("Ses işlenirken hata oluştu.")
        except Exception as e:
            st.error(f"Bağlantı hatası: {e}")

# 2. Durum: Yazılı Giriş Var mı? (Eğer ses yoksa yazıya bak)
if prompt and not final_prompt:
    final_prompt = prompt

# --- SOHBET AKIŞI ---
if final_prompt:
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": final_prompt})
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
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                message_placeholder.markdown("❌ Sunucu hatası.")
        except Exception as e:
            message_placeholder.markdown(f"❌ Bağlantı hatası: {e}")