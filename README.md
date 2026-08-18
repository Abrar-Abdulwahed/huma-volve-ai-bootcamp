# Telecom RAG API

A production-oriented **Retrieval-Augmented Generation (RAG)** microservice for telecom
customer support, built with **FastAPI**, **LangChain**, **FAISS**, and **Google Gemini**.

Documents are embedded with a multilingual sentence-transformer model, stored in a local
FAISS index, and retrieved at query time to ground Gemini's answers in your own knowledge base.

---

## Tech Stack

| Layer            | Technology                                             |
| ---------------- | ------------------------------------------------------ |
| API framework    | FastAPI + Uvicorn                                       |
| Orchestration    | LangChain (`langchain`, `langchain-community`, `-core`)|
| Embeddings       | `sentence-transformers` (HuggingFace, CPU)             |
| Vector store     | FAISS (`faiss-cpu`)                                     |
| LLM              | Google Gemini (`langchain-google-genai`)               |
| Config / secrets | YAML (`config/config.yml`) + `.env` (`python-dotenv`)  |

---

## Requirements

- Python **3.11**
- A Google **Gemini API key** (`GOOGLE_API_KEY`)

---

## Setup

From the project root (`telecom-rag/`):

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
#    If you get an execution-policy error, run once:
#    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 3. Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> On macOS/Linux, activate with `source .venv/bin/activate` instead.

### Configure secrets

Copy the example env file and add your key:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```dotenv
GOOGLE_API_KEY="your_real_gemini_api_key"
```

Application settings (models, chunking, retrieval `k`, index path) live in
[`config/config.yml`](config/config.yml) and can be edited without touching code.

---

## Running the app

With the virtual environment activated:

```powershell
uvicorn main:app --reload --port 8000
```

Or without activating it:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

`main.py` also has an entrypoint, so `python main.py` works too.

Once running:

- Health check: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

---

## Configuration reference (`config/config.yml`)

```yaml
app:
  name: "Telecom RAG API"
  version: "1.0.0"

data:
  vector_index_path: "faiss_telecom_index"  # where the FAISS index is persisted
  chunk_size: 500
  chunk_overlap: 100
  batch_size: 50

models:
  embedding_provider: "huggingface"
  embedding_model_name: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  llm_provider: "gemini"
  llm_model_name: "gemini-2.5-flash"
  temperature: 0
  k_retrieval: 20
```

---

## Project structure

```
telecom-rag/
├── main.py                     # FastAPI app, lifespan, health endpoint
├── requirements.txt
├── config/
│   └── config.yml              # App/model/data settings
├── src/
│   ├── config/config_parser.py # Loads config.yml + .env into a `settings` object
│   ├── core/factories.py       # ModelFactory: builds embeddings & Gemini LLM
│   ├── logging/logger.py       # Rotating file + console logger
│   ├── vectorstore/            # FAISS repository (ingest/search/persist)
│   └── routers/                # /ingest and /query API routers
└── .env                        # GOOGLE_API_KEY (not committed)
```

---

## Notes

- The FAISS index is written to `faiss_telecom_index/` (git-ignored). Ingest documents
  before querying, or the query endpoint will report an empty vector store.
- The first run downloads the sentence-transformer model, which may take a moment.
- Secrets (`.env`), logs (`*.log`), the FAISS index, and `__pycache__/` are excluded via
  [`.gitignore`](.gitignore).
