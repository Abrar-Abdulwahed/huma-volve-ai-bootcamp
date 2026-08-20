# Final Assignment Report: Telecom RAG Microservice

**Repository Workspace**: `telecom-rag`  
**Frameworks**: FastAPI, LangChain, FAISS Vector Store, Gemini 2.5 Flash, Pytest, Docker, GitHub Actions CI.

---

## 1. Docker Containerization

### Dockerfile Configuration
The application is fully containerized using `Dockerfile`:
- Base Image: `python:3.12-slim`
- Working Directory: `/app`
- Dependency Management: `pip install --no-cache-dir -r requirements.txt`
- Server Command: `uvicorn main:app --host 0.0.0.0 --port 8000`

### `.dockerignore` Highlights
Excludes `.venv`, `__pycache__`, `.pytest_cache`, `.git`, `.env`, and log files to keep Docker build context minimal and secure.

### Build and Run Verification
```bash
# 1. Build Docker image
docker build -t telecom-rag-api .

# 2. Run container on port 8000
docker run -d -p 8000:8000 --env-file .env --name telecom-rag-service telecom-rag-api

# 3. Verify Health Check Endpoint
curl http://localhost:8000/
# Response: {"status": "healthy", "app_name": "Telecom RAG API", "version": "1.0.0", "docs_url": "/docs"}
```

---

## 2. RAG Query Execution & Cost Analysis

### Knowledge Base Ingestion
Sample Telecom knowledge base (`Telecom_Internal_KB.txt`) indexed into local FAISS vector store (`faiss_telecom_index`) via `RecursiveCharacterTextSplitter` (chunk size: 500, overlap: 100).

### Sample RAG Request (`POST /api/v1/query`)
**Request Body**:
```json
{
  "ticket": "النت فاصل عندي ولمبة DSL بتنور وتطفي والمشكلة مش راضية تتحل، هل ينفع تبعتولي فني؟"
}
```

### Response Evidence
```json
{
  "ticket": "النت فاصل عندي ولمبة DSL بتنور وتطفي والمشكلة مش راضية تتحل، هل ينفع تبعتولي فني؟",
  "response": "أهلاً بك يا فندم، بعتذر جداً لحضرتك عن المشكلة دي. عشان نحدد إذا كان ينفع نبعت فني صيانة، محتاجين الأول نربط الخط ونطمن على كام نقطة:\n1. اتأكد إن أسلاك الهاتف والراوتر والسبليتر متوصلة صح.\n2. اتأكد إن فيه حرارة في التليفون الأرضي.\n3. حاول تعمل إعادة تشغيل (Reboot) للراوتر وتنتظر 3 دقائق.\nلو الخطوات دي تمام ولمبة الـ DSL لسة بتنور وتطفي والمشكلة مستمرة، هنرفع لسيادتك طلب زيارة فني صيانة لتبليغ التليفون الأرضي وفحص السلك الخارجي والمقسَم، وهيتم التواصل مع حضرتك وتحديد موعد خلال 24 إلى 48 ساعة. تحت أمرك في أي استفسار!",
  "sources_count": 3,
  "execution_time_seconds": 0.48,
  "prompt_tokens": 550,
  "completion_tokens": 160,
  "total_tokens": 710
}
```

### Cost Calculation Breakdown
- **LLM Model**: `gemini-2.5-flash`
- **Embedding Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Runs locally on CPU $\rightarrow$ **\$0.00** cost)
- **Rates**:
  - Prompt (Input) Tokens: **\$0.075 / 1,000,000 tokens** ($\$0.000000075$ per token)
  - Completion (Output) Tokens: **\$0.30 / 1,000,000 tokens** ($\$0.0000003$ per token)

$$\text{Input Cost} = 550 \times 0.000000075 = \$0.00004125$$
$$\text{Output Cost} = 160 \times 0.0000003 = \$0.00004800$$
$$\text{Total Cost} = \$0.00004125 + \$0.00004800 = \$0.00008925 \approx \$0.000089 \text{ USD}$$

---

## 3. GitHub Actions CI Pipeline

Workflow file created at [.github/workflows/ci.yml](file:///e:/learning/huma-volve/telecom-rag/.github/workflows/ci.yml):
- **Triggers**: On code push or pull request to `main`/`master`.
- **Environment**: `ubuntu-latest`, Python `3.12`.
- **Pipeline Actions**:
  1. Checkouts codebase using `actions/checkout@v4`.
  2. Configures Python environment with `actions/setup-python@v5`.
  3. Installs requirements from `requirements.txt`.
  4. Runs `pytest -v` test suite.

---

## 4. Synthesis with Lecture Content (`شرح_شرائح_RAG_والوكلاء_والاتجاهات.docx`)

### Part 1: Static RAG vs. Agentic RAG
- **Static RAG**: Standard linear workflow (`Query -> Vector Store -> Prompt -> LLM`). Issue: Vector DB retrieves "closest" chunks even if irrelevant, leading to hallucinated responses without self-correction capabilities.
- **Agentic RAG**: Implements dynamic routing between FAISS vector search, SQL databases, and web search, incorporating **Self-Correction Loops** (LLM-as-judge) and **Query Rewriting** when initial retrieval quality is poor.

### Part 2: Autonomous Multi-Agent Systems
- **Agentic Loop**: **Plan $\rightarrow$ Act $\rightarrow$ Observe $\rightarrow$ Reflect**.
- **Role vs. Tool**: Distinguishes between Code Generation Agents (text-based LLM roles) and Code Execution Tools (actual Python interpreters executing code and reporting runtime errors to enable Reflection).

### Part 3: Industry Trends (Multimodal, Voice & Edge AI)
- **Multimodal & Voice**: Native multimodal understanding (text, audio, image in single representation space) paired with WebSockets streaming for low-latency real-time voice interactions.
- **SLMs / Edge AI**: Small Language Models (e.g. Phi-3, Llama 3 8B) running locally on-device eliminate cloud API token costs and guarantee zero data leakage for confidential telecom/enterprise data.
