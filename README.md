# Intent Detection & RAG AI Assistant

Bu proje, kullanıcı niyetini (intent) algılayarak en uygun cevabı veren; **sesli/yazılı sohbet**, web araması ve döküman analizi yeteneklerine sahip gelişmiş bir yapay zeka asistanıdır.

## 🚀 Özellikler

*   **🎙️ Sesli Sohbet (Speech-to-Text):** Google Gemini 2.5 Flash modeli ile güçlendirilmiş ses tanıma özelliği sayesinde asistanla sesli konuşabilirsiniz.
*   **🗂️ Sohbet Yönetimi (History):** Yan menü (sidebar) üzerinden yeni sohbet başlatabilir, eski sohbetleriniz arasında geçiş yapabilir veya silebilirsiniz.
*   **Akıllı Niyet Algılama (Intent Detection):** Kullanıcının sorusunu analiz eder ve üç kategoriden birine sınıflandırır:
    *   **Genel Sohbet (`general_chat`):** Günlük konuşmalar ve selamlaşmalar.
    *   **Web Araması (`web_search_query`):** Güncel bilgiler, hava durumu, fiyatlar veya etkinlikler için internet araması (Google SerpAPI).
    *   **Döküman Analizi (`document_qa`):** Yüklenen PDF, TXT veya MD dosyaları üzerinde soru-cevap (RAG).
*   **Hibrit Sınıflandırma:** Kural tabanlı (Rule-based) ve Yapay Zeka (Zero-shot classification) tabanlı hibrit bir intent algılama mekanizması kullanır.
*   **RAG (Retrieval-Augmented Generation):** Yüklenen dökümanları vektör veritabanına (ChromaDB) kaydeder ve bağlam odaklı cevaplar üretir.
*   **Modern Arayüz:** Hem **React (Vite)** hem de **Streamlit** ile geliştirilmiş iki farklı kullanıcı arayüzü seçeneği sunar.
*   **Güçlü Arka Uç:** FastAPI tabanlı hızlı ve modüler backend.
*   **Yerel LLM Desteği:** Ollama üzerinden `gemma3:4b` modelini kullanır.

## 🛠️ Teknolojiler

*   **Backend:** FastAPI, Google Gemini API (STT)
*   **Frontend:** 
    *   **React:** Vite, Tailwind CSS (Önerilen)
    *   **Streamlit:** streamlit-mic-recorder (Hızlı kullanım için)
*   **LLM:** Ollama (Gemma 3 4B)
*   **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
*   **Vector DB:** ChromaDB
*   **Search:** SerpAPI (Google Search)
*   **Intent Model:** `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`

## 📋 Gereksinimler

Projenin çalışması için aşağıdaki araçların kurulu olması gerekmektedir:

1.  **Python 3.10+**
2.  **Ollama:** Bilgisayarınızda [Ollama](https://ollama.com/) kurulu ve çalışıyor olmalıdır.
    *   Gerekli modeli indirmek için terminalde şu komutu çalıştırın:
        ```bash
        ollama run gemma3:4b
        ```
3.  **API Anahtarları:**
    *   **SerpAPI:** Google aramaları için [SerpAPI](https://serpapi.com/).
    *   **Google Gemini 2.5 Flash API:** Sesli sohbet (STT) özelliği için [Google AI Studio](https://aistudio.google.com/).

## ⚙️ Kurulum

1.  **Projeyi Klonlayın:**
    ```bash
    git clone <repo-url>
    cd intent_detection
    ```

2.  **Sanal Ortam Oluşturun (Önerilen):**
    ```bash
    python -m venv venv
    # Windows için:
    venv\Scripts\activate
    # Linux/Mac için:
    source venv/bin/activate
    ```

3.  **Gerekli Kütüphaneleri Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Çevre Değişkenlerini Ayarlayın:**
    *   Proje ana dizininde `.env` adında bir dosya oluşturun.
    *   İçerisine API anahtarlarınızı ekleyin:
        ```env
        SERPAPI_KEY=senin_serpapi_anahtarin
        GOOGLE_API_KEY=senin_google_gemini_anahtarin
        ```

## ▶️ Çalıştırma

Projenin çalışması için hem backend hem de frontend uygulamalarını ayrı terminallerde başlatmanız gerekmektedir.

### 1. Backend'i Başlatın
API sunucusunu ayağa kaldırmak için:
```bash
uvicorn main:app --reload
```
*Backend `http://localhost:8000/docs` adresinde çalışacaktır.*

### 2. Frontend'i Başlatın (Seçenek 1: React - Önerilen)
Yeni bir terminal açın ve frontend dizinine giderek bağımlılıkları yükleyip uygulamayı başlatın:
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios react-markdown lucide-react
```
*Tarayıcınızda otomatik olarak `http://localhost:5173` adresi açılacaktır.*

### 3. Frontend'i Başlatın (Seçenek 2: Streamlit)
Yeni bir terminal açın (sanal ortamın aktif olduğundan emin olun) ve arayüzü başlatın:
```bash
streamlit run app.py
```
*Tarayıcınızda otomatik olarak `http://localhost:8501` adresi açılacaktır.*

## 📂 Proje Yapısı

```
intent_detection/
├── frontend/           # React Frontend (Vite + Tailwind)
├── app.py              # Streamlit Frontend (Alternatif UI)
├── main.py             # FastAPI Backend (Intent, RAG, STT)
├── requirements.txt    # Python kütüphane bağımlılıkları
├── .env                # API anahtarları (siz oluşturmalısınız)
└── chroma_db/          # Vektör veritabanı dosyaları (otomatik oluşur)
```