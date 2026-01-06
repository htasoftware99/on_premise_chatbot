import os
import shutil
from typing import List, Optional
from datetime import datetime 
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from transformers import pipeline

# --- IMPORTLAR ---
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationChain, RetrievalQA
from langchain_classic.prompts import PromptTemplate

# Community araçları
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma

# Entegrasyonlar
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
# Text Splitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

import google.generativeai as genai

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OLLAMA_MODEL = "gemma3:4b"  
CHROMA_PATH = "./chroma_db"

# --- GEMINI YAPILANDIRMASI (STT İçin) ---
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("UYARI: GOOGLE_API_KEY bulunamadı. Sesli sohbet çalışmayabilir.")

# --- BAŞLANGIÇ AYARLARI ---
app = FastAPI()
os.environ["SERPAPI_API_KEY"] = SERPAPI_KEY

# --- PROMPTLAR ---
GENERAL_RAG_PROMPT = """
Sen uzman bir döküman asistanısın.
Görevin: Aşağıda verilen "Bağlam (Context)" içindeki bilgileri kullanarak kullanıcının sorusunu cevaplamaktır.

Kurallar:
1. Sadece ve sadece verilen bağlamdaki bilgilere göre cevap ver.
2. Döküman dışından bilgi uydurma.
3. Eğer sorunun cevabı dökümanda yoksa, net bir şekilde "Bu bilgi yüklenen dökümanda yer almıyor" de.
4. Cevabı verirken dökümandaki üsluba uygun, profesyonel ve açıklayıcı ol.

Bağlam (Context):
{context}

Kullanıcı Sorusu: {question}

Cevap:
"""

SEARCH_PROMPT_TEMPLATE = """
Sen yardımsever bir asistansın.
Bugünün Tarihi: {current_date}

Aşağıda Google arama sonuçları verilmiştir. Bu bilgileri kullanarak kullanıcının sorusunu cevapla.
DİKKAT: Arama sonuçlarındaki tarihleri kontrol et. Eğer etkinlik geçmişte kalmışsa o bilgiyi kullanma.
Sadece gelecekteki güncel etkinlikleri veya bilgileri ver.

Kullanıcı Sorusu: {question}
Arama Sonuçları: {search_result}

Cevap:
"""

CHAT_PROMPT = """
Sen yardımsever bir yapay zeka asistanısın.
Kullanıcıya nazik, kısa ve öz cevaplar ver.
Bilmediğin veya emin olmadığın konularda dürüst ol.
"""

llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.3)

# Intent Detection (mDeBERTa Model)
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", device=-1)

def detect_intent(text: str) -> str:
    # Model Etiketleri
    labels = [
        "general conversation, greeting, self-introduction, or asking about the assistant's identity",
        "internet search regarding public figures, news, weather, prices, events, concerts, or objective facts",
        "question specific to the uploaded file or document analysis"
    ]
    
    result = classifier(text, labels)
    top_label = result['labels'][0]
    
    print(f"DEBUG (Model): Algılanan Etiket -> '{top_label}'")

    if "internet search" in top_label:
        return "web_search_query"
    elif "uploaded file" in top_label:
        return "document_qa"
    else:
        return "general_chat"

memory = ConversationBufferMemory(return_messages=True)
search = SerpAPIWrapper()

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})
vector_store = None 

# --- MODELLER ---
class QueryRequest(BaseModel):
    query: str

class ResponseModel(BaseModel):
    response: str
    intent: str
    source: str

# --- ENDPOINTLER ---

# YENİ ENDPOINT: Ses dosyasını metne çevir (Gemini ile)
@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        print(f"🎤 Ses dosyası alındı: {file.filename}")
        print(f"ℹ️ Dosya Tipi: {file.content_type}")
        
        # Dosyayı belleğe oku
        audio_bytes = await file.read()
        
        # Model Tanımla
        print("🤖 gemini-2.5-flash modeli yükleniyor...")
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Modele gönder
        print("📤 Ses verisi Google'a gönderiliyor...")
        response = model.generate_content([
            "Aşağıdaki ses dosyasındaki konuşmaları birebir metne çevir. Sadece duyduğun kelimeleri yaz, başka hiçbir açıklama, yorum veya komut tekrarı yapma.",
            {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
        ])
        
        print(f"✅ Çeviri Başarılı: {response.text[:50]}...") # İlk 50 karakteri logla
        return {"text": response.text.strip()}
    
    except Exception as e:
        # HATAYI BURADA GÖRECEĞİZ
        print(f"❌ KRİTİK HATA: {e}")
        # Hatanın detayını frontend'e de gönderelim
        raise HTTPException(status_code=500, detail=f"Sunucu Hatası: {str(e)}")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global vector_store
    try:
        # Dosyayı geçici olarak kaydet
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Dosya uzantısına göre Loader seçimi
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            # .txt veya .md varsayıyoruz
            loader = TextLoader(file_path, encoding="utf-8")
            
        documents = loader.load()
        
        # Chunklara böl
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # Vektör veritabanına göm
        vector_store = Chroma.from_documents(
            documents=chunks, 
            embedding=embeddings, 
            persist_directory=CHROMA_PATH
        )
        
        os.remove(file_path) # Temizlik
        return {"message": f"{file.filename} başarıyla analiz edildi."}
    except Exception as e:
        return {"error": str(e)} # Hata durumunda json dönmeli

@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: QueryRequest):
    user_query = request.query.lower() # Küçük harfe çevir
    
    # --- 1. AŞAMA: KESİN KURALLAR (RULE-BASED) ---
    # Modelin hata yapmasını engellemek için bariz kelimeleri elle yakalıyoruz.
    
    # A) Sohbet Zorlayıcılar (Model search sanmasın diye)
    greeting_keywords = ["merhaba", "selam", "günaydın", "iyi geceler", "kimsin", "adın ne", "sen kimsin", "nasılsın", "naber", "benim adım", "ben hasan"]
    
    # B) Arama Zorlayıcılar (Model chat sanmasın diye) -> BURASI YENİ
    search_keywords = ["konser", "bilet", "maç", "etkinlik", "hava durumu", "dolar", "euro", "altın", "kaç tl", "kaç para", "fiyatı", "nerede", "ne zaman", "kimdir", "nedir"]

    intent = ""

    if any(k in user_query for k in greeting_keywords):
        intent = "general_chat"
        print(f"DEBUG (Rule): Keyword ile CHAT seçildi.")
        
    elif any(k in user_query for k in search_keywords):
        intent = "web_search_query"
        print(f"DEBUG (Rule): Keyword ile SEARCH seçildi.")
        
    else:
        # --- 2. AŞAMA: YAPAY ZEKA KARARI ---
        # Kelime listelerinde yoksa modele sor (Örn: "Karnım ağrıyor", "Şiir yaz")
        intent = detect_intent(request.query)
    
    # --- 3. AŞAMA: DOSYA KONTROLÜ ---
    if intent == "document_qa" and vector_store is None:
        intent = "general_chat"

    response_text = ""
    source_used = ""

    # --- 4. AŞAMA: İŞLEM ---
    today = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year

    if intent == "web_search_query":
        print(f"--> Intent: Web Search ({request.query})")
        try:
            enriched_query = f"{request.query} {current_year}"
            
            print(f"   (Google Query: {enriched_query})")
            
            search_result = search.run(enriched_query)
            
            if not search_result or len(search_result) < 5:
                search_result = search.run(request.query)

            final_prompt = SEARCH_PROMPT_TEMPLATE.format(
                current_date=today, 
                question=request.query, 
                search_result=search_result
            )
            
            response_text = llm.invoke(final_prompt)
            source_used = "SerpApi (Google)"
            
        except Exception as e:
            print(f"Search Hatası: {e}")
            response_text = llm.invoke(request.query)
            intent = "general_chat"
            source_used = "LLM (Search Başarısız)"

    elif intent == "document_qa" and vector_store is not None:
        print(f"--> Intent: RAG ({request.query})")
        retriever = vector_store.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff", 
            retriever=retriever,
            chain_type_kwargs={"prompt": PromptTemplate(
                template=GENERAL_RAG_PROMPT,
                input_variables=["context", "question"]
            )}
        )
        response_text = qa_chain.run(request.query)
        source_used = "Yüklenen Döküman (RAG)"
        
    else:
        print(f"--> Intent: Chat ({request.query})")
        
        template = f"""{CHAT_PROMPT}
        
        Geçmiş Sohbet:
        {{history}}
        
        Kullanıcı: {{input}}
        Asistan:"""
        
        PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
        
        conversation = ConversationChain(
            prompt=PROMPT,
            llm=llm, 
            memory=memory
        )
        response_text = conversation.predict(input=request.query)
        source_used = "LLM + Hafıza"

    return {
        "response": response_text,
        "intent": intent,
        "source": source_used
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)