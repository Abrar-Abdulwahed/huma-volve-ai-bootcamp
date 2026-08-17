# Telecom RAG - Day 2 Assignment

A Retrieval-Augmented Generation (RAG) system for a telecom customer-service desk. An agent's ticket (in Egyptian Arabic) is answered instantly from a 500-page internal knowledge base instead of a manual 5-minute lookup - reducing Average Handling Time (AHT) and SLA breaches.

**Stack:** LangChain - FAISS - multilingual embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) - Gemini `gemini-2.5-flash`.

---

## Index

### Assignment deliverables
| Task | Report | Supporting notebook |
|---|---|---|
| **Task 1 - Prompt Engineering** (3 system prompts w/ negative constraints) | [reports/Task1_Prompt_Engineering.md](reports/Task1_Prompt_Engineering.md) | [notebooks/01_telecom_rag_demo.ipynb](notebooks/01_telecom_rag_demo.ipynb) |
| **Task 2 - Chunking Strategy: Semantic Chunking** | [reports/Task2_Chunking_Strategy.md](reports/Task2_Chunking_Strategy.md) | [notebooks/02_task2_semantic_chunking.ipynb](notebooks/02_task2_semantic_chunking.ipynb) |

### Data
- [data/Telecom_Internal_KB.txt](data/Telecom_Internal_KB.txt) - the internal knowledge base (SLA policy, 200 router specs, 300 error codes, escalation matrix).

---

## Task 1 - Prompt Engineering (Negative Constraints)

Three system prompts, each **adding one negative constraint**, tested on the same two tickets to show how the output changes:

| Version | Added constraint | Failure mode it removes |
|---|---|---|
| **V1** | only "no real telco name" | (baseline - leaks, hallucinates, formal tone) |
| **V2** | + "use context only / don't invent" | stops **hallucination** (invented DNS steps, fake causes) |
| **V3** | + "don't reveal internals / Egyptian-only" | stops **internal-data leak** (ext. 111) + fixes **tone** |

**Key insight:** negative constraints are *additive* - one failure mode needs one dedicated constraint. -> [full report](reports/Task1_Prompt_Engineering.md)

## Task 2 - Chunking Strategy (prove a chunk the original missed)

Baseline = `RecursiveCharacterTextSplitter(500/100)`. The alternative strategy recovers a chunk the baseline missed:

| Alternative | Wins on | Proof |
|---|---|---|
| **Semantic Chunking** | coherent multi-fact **policy** | retrieves the whole SLA policy (dispatch `6dB` **+** compensation `72h`) in one chunk; recursive splits it apart -> [report](reports/Task2_Chunking_Strategy.md) |

**Key insight:** the chunking strategy must match the **structure of the data** - semantic chunking keeps a coherent policy whole (wins on multi-fact prose) but merges dense repetitive records (loses on error-code lookups). The report includes an **end-to-end business-impact** section showing the same prompt + LLM give a *complete/correct* vs *incomplete/wrong* answer depending only on chunking.

---

## How to run

**Notebook 01** runs locally. **Notebooks 02 & 03** are Colab-ready (a `%pip install` cell + a file-upload cell at the top).

### Google Colab (recommended for 02 / 03)
1. Open the notebook in Colab.
2. Run **Cell 0** (installs libraries; click *RESTART RUNTIME* if prompted, then re-run).
3. Run **Cell 1** -> upload `data/Telecom_Internal_KB.txt` when prompted (confirm it shows ~149,000 bytes).
4. For the end-to-end LLM cells, paste a **Gemini API key** (starts with `AIza`, from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)) when prompted.
5. **Runtime -> Run all.**

### Local (Python 3.11 + venv)
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -U langchain langchain-community langchain-core \
  langchain-google-genai langchain-huggingface langchain-text-splitters \
  langchain-experimental sentence-transformers faiss-cpu python-dotenv tqdm ipykernel
```
- Put your key in `notebooks/.env` as `GOOGLE_API_KEY="AIza..."` (Task 1 / end-to-end LLM cells).
- Task 2 **retrieval proofs need no API key** - only local embeddings + FAISS.

---

## Repository structure
```
RAG_Demo_Notebook/
├── README.md                                  <- this index
├── data/
│   └── Telecom_Internal_KB.txt                <- knowledge base
├── notebooks/
│   ├── 01_telecom_rag_demo.ipynb              <- base RAG + Task 1
│   ├── 02_task2_semantic_chunking.ipynb       <- Task 2 (Semantic Chunking)
│   └── 03_task2_markdown_chunking.ipynb       <- supplementary (MarkdownHeader experiment)
└── reports/
    ├── Task1_Prompt_Engineering.md
    └── Task2_Chunking_Strategy.md             <- Semantic + business impact
```
