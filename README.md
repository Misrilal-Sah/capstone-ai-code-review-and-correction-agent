<div align="center">

```
 ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ███████╗██╗   ██╗██╗███████╗██╗    ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔════╝██║   ██║██║██╔════╝██║    ██║
██║     ██║   ██║██║  ██║█████╗      ██████╔╝█████╗  ██║   ██║██║█████╗  ██║ █╗ ██║
██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗██╔══╝  ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║███████╗ ╚████╔╝ ██║███████╗╚███╔███╔╝
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝
```

### ✦ AI-Powered Code Review & RAG Knowledge Agent ✦
### *Autonomous · Reflective · Multi-LLM · CLI-First*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Pro-Primary_LLM-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Groq](https://img.shields.io/badge/Groq-llama--3.1--8b-F54E42?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-7124_Chunks-FF6B35?style=for-the-badge)](https://trychroma.com)
[![LangChain](https://img.shields.io/badge/LangChain-RAG_Pipeline-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)

[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production_Ready-22C55E?style=for-the-badge)]()
[![AST Rules](https://img.shields.io/badge/AST_Rules-24_Checks-8B5CF6?style=for-the-badge)]()
[![Confidence](https://img.shields.io/badge/Self_Reflection-3_Iterations-F59E0B?style=for-the-badge)]()

<br/>

> **Two agents. One codebase. Zero compromise.**
> Drop in any Python file, folder, git diff, or GitHub PR — and get an expert-grade review,
> corrected source code, and a full audit trail. Ask anything about Python best practices
> and get RAG-grounded answers from a 7,124-chunk knowledge base.

<br/>

</div>

---

## ⚡ What Is This?

An **autonomous AI agentic system** built around two production-grade CLI tools that share a common RAG infrastructure. Point the Code Review Agent at any Python source — file, folder, git diff, or live GitHub PR — and receive a full markdown report, corrected source code, and an audit log. Open the RAG Chatbot to query a curated 7,124-chunk knowledge base of Python best-practice documents, answered with source citations, confidence scores, and letter grades.

```
┌─────────────────────────────────────────────┐
│  TWO ENTRY POINTS                           │
│                                             │
│  $ python code_review_main.py  →  🔍 Review │
│  $ python rag_main.py          →  🤖 Chat   │
└─────────────────────────────────────────────┘
```

| Capability | Details |
|---|---|
| 🧠 Multi-LLM Fallback | Gemini 2.5 Pro → Groq → Flash → OpenRouter → FLAN-T5 |
| 🔍 Static Analysis | 24 AST-based rules, Pylint + Black integration |
| 📚 Knowledge Base | 22 PDFs + 2 video transcripts = 7,124 indexed chunks |
| 🔄 Self-Reflection | Up to 3 iterations, auto-refine if confidence < 70% |
| 🛡️ Sandbox Validation | `compile()` + Black + Pylint before presenting any fix |
| 🐙 Git / GitHub Native | Diff review, commit review, live PR review via API |

---


---

## 🏗️ System Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                              ❯  USER  INPUT                                 ║
║   ┌────────────────────────────┐          ┌──────────────────────────────┐  ║
║   │  Question / Query          │          │  File · Folder · Git · PR    │  ║
║   └────────────┬───────────────┘          └───────────────┬──────────────┘  ║
╚════════════════╪═══════════════════════════════════════════╪════════════════╝
                 │                                           │
                 ▼                                           ▼
  ╔══════════════════════════╗         ╔══════════════════════════════════════╗
  ║   🤖  RAG CHATBOT AGENT  ║         ║       🔍  CODE REVIEW AGENT         ║
  ║   python rag_main.py     ║         ║       python code_review_main.py    ║
  ║                          ║         ║                                     ║
  ║  Tools                   ║         ║  Tools                              ║
  ║  ├─ knowledge_search     ║         ║  ├─ file_reader                     ║
  ║  ├─ clarify_question     ║         ║  ├─ static_analysis_helper          ║
  ║  ├─ summarize_context    ║         ║  ├─ markdown_writer                 ║
  ║  └─ provide_sources      ║         ║  └─ sandbox_validator               ║
  ║                          ║         ║                                     ║
  ║  Pipeline                ║         ║  Pipeline                           ║
  ║  ├─ Reason               ║         ║  ├─ Read  →  AST (24 rules)        ║
  ║  ├─ Search (5 chunks)    ║         ║  ├─ RAG retrieval                   ║
  ║  ├─ Generate             ║         ║  ├─ LLM Generate                    ║
  ║  ├─ Reflect  ×3          ║         ║  ├─ Reflect  ×3                     ║
  ║  └─ Grade  (A–F)         ║         ║  └─ Sandbox validate                ║
  ╚══════════════╦═══════════╝         ╚═══════════════════╦══════════════════╝
                 ║                                         ║
                 ╚═══════════════════╦═════════════════════╝
                                     ║
               ╔═════════════════════╩══════════════════════╗
               ║         🔗  SHARED  INFRASTRUCTURE         ║
               ║                                            ║
               ║  ┌─────────────────────────────────────┐  ║
               ║  │  Multi-LLM Fallback Chain           │  ║
               ║  │  1. Gemini 2.5 Pro   (primary)      │  ║
               ║  │  2. Groq llama-3.1   (fast)         │  ║
               ║  │  3. Gemini 2.5 Flash (backup)       │  ║
               ║  │  4. OpenRouter #1    (free tier)     │  ║
               ║  │  5. OpenRouter #2    (free tier)     │  ║
               ║  │  6. FLAN-T5 local    (no API key)   │  ║
               ║  └─────────────────────────────────────┘  ║
               ║                                            ║
               ║  ┌─────────────────────────────────────┐  ║
               ║  │  RAG Pipeline                       │  ║
               ║  │  PDF/MP4 → Chunk → Embed →          │  ║
               ║  │  ChromaDB (7,124 chunks)            │  ║
               ║  │  all-MiniLM-L6-v2 embeddings        │  ║
               ║  └─────────────────────────────────────┘  ║
               ╚══════════════════════╦═════════════════════╝
                                      ║
               ╔══════════════════════╩═════════════════════╗
               ║                  📤  OUTPUT                 ║
               ║  ┌────────────────────┐  ┌───────────────┐ ║
               ║  │ Answer + Sources   │  │ codereview.md │ ║
               ║  │ Confidence + Grade │  │ corrected_*.py│ ║
               ║  └────────────────────┘  │ audit_log.json│ ║
               ║                          └───────────────┘ ║
               ╚════════════════════════════════════════════╝
```

> Full Mermaid diagram available in [`architecture.mmd`](architecture.mmd)

---

## 🎬 Live CLI Demo

### Code Review Agent

```bash
$ python code_review_main.py review ./samples/python/bad_code_smells.py
```

```
╔══════════════════════════════════════════════════════════════╗
║   🔍  CODE REVIEW AGENT  ·  bad_code_smells.py              ║
╚══════════════════════════════════════════════════════════════╝

 [1/7]  📂  Reading file ................ bad_code_smells.py
 [2/7]  🔬  Running static analysis ..... 33 issues found
              ├─ CRITICAL  ×  4   (SQL injection, bare secrets)
              ├─ MAJOR     × 17   (missing docstrings, deep nesting)
              └─ MINOR     × 12   (magic numbers, style)
 [3/7]  📚  Retrieving best practices ... 5 RAG chunks matched
 [4/7]  🧠  Generating review ........... ✓ Groq llama-3.1-8b-instant
 [5/7]  🔄  Self-reflection ............. iteration 1 → confidence 0.85
 [6/7]  🛡️   Sandbox validation .......... ✓ Black  ✓ Pylint  ✓ compile()
 [7/7]  📝  Writing outputs .............
              ├─ ✓  codereview.md
              ├─ ✓  corrected_bad_code_smells.py
              └─ ✓  audit_log.json

╔══════════════════════════════════════════════════════════════╗
║   ✅  Review complete   ·   Confidence: 90.0%               ║
╚══════════════════════════════════════════════════════════════╝
```

### RAG Chatbot Agent

```bash
$ python rag_main.py ask "What are the production Do's for RAG?" --verbose
```

```
╔══════════════════════════════════════════════════════════════╗
║   🤖  RAG CHATBOT AGENT                                     ║
╚══════════════════════════════════════════════════════════════╝

 [Step 1]  💭  Reasoning about the question ...
 [Step 2]  🔎  Searching knowledge base ........  5 chunks found
 [Step 3]  ✍️   Generating answer ...
 [Step 4]  🔄  Self-reflecting .................. confidence: 0.85
 [Step 5]  📊  Evaluating quality .............. Grade: B  (score: 0.82)

 ┌─────────────────────────────────────────────────────────┐
 │  Answer                                                 │
 │  1. Use hybrid search (vector + keyword)               │
 │  2. Implement smart chunking strategies                 │
 │  3. Add metadata filtering for relevance               │
 │  4. Cache frequent queries                             │
 │  5. Monitor hallucination rates in production          │
 │                                                        │
 │  Sources: RAG_Best_Practices.pdf, Production_ML.pdf    │
 └─────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════╗
║   ✅  Response generated   ·   Confidence: 0.85            ║
╚══════════════════════════════════════════════════════════════╝
```

---

## ✨ Feature Deep-Dive

<details>
<summary><b>🔍 Code Review Agent — everything it can do</b></summary>

### Multi-Source Input
| Input Type | Command | Notes |
|---|---|---|
| Single file | `review file.py` | Any `.py` file |
| Entire folder | `review ./src/` | Recursive |
| Uncommitted changes | `review-changes` | Tracked modified files |
| Staged changes | `review-changes --staged` | After `git add` |
| Specific commit | `review-commit <hash>` | SHA or ref |
| GitHub PR | `review-pr <#> --repo owner/repo` | Requires `GITHUB_TOKEN` |

### AST Static Analysis (24 Rules)
| Severity | Rules |
|---|---|
| 🔴 **Critical** | SQL injection patterns, hardcoded secrets/passwords, eval() usage |
| 🟠 **Major** | Missing docstrings, bare `except`, unused imports, deep nesting (>4) |
| 🟡 **Minor** | Long functions (>20 lines), magic numbers, missing type hints |

### 3-Step Output
```
code_review_output/
├── codereview.md          ← Markdown report with inline annotations
├── corrected_*.py         ← Fixed source with explanatory comments
└── audit_log.json         ← Immutable audit trail (hash, LLM, rules)
```

</details>

<details>
<summary><b>🤖 RAG Chatbot Agent — knowledge base & evaluation</b></summary>

### Knowledge Base (7,124 Chunks)
- **22 PDF documents** — Clean Code, Design Patterns, Security, OOP, RAG
- **2 Video transcripts** — Whisper-transcribed (RAG + GenAI Databases)
- **Embeddings** — `all-MiniLM-L6-v2` via SentenceTransformers
- **Vector DB** — ChromaDB with persistent local storage

### Evaluation Metrics
| Metric | Measured By |
|---|---|
| **Relevance** | Semantic similarity of answer to question |
| **Groundedness** | Claims traceable to retrieved source chunks |
| **Clarity** | Structure, readability, formatting |
| **Completeness** | All question aspects addressed |
| **Grade** | Composite A–F letter grade |

### Tools Available to the Agent
```python
knowledge_search(query)      # Semantic search over 7,124 chunks
clarify_question(question)   # Rephrase for better retrieval
summarize_context(text)      # Compress long retrieved contexts
provide_sources(chunks)      # Format inline citations
```

</details>

<details>
<summary><b>🧠 Multi-LLM Fallback Chain</b></summary>

The system tries each provider in priority order and falls back automatically on error or timeout:

```
Priority  Provider              Model                  Tier
────────  ───────────────────── ──────────────────── ────────
  1       Google Gemini         gemini-2.5-pro        API Key
  2       Groq                  llama-3.1-8b-instant  API Key (free)
  3       Google Gemini         gemini-2.5-flash      API Key
  4       OpenRouter            kat-coder-pro         API Key (free)
  5       OpenRouter            nova-2-lite           API Key (free)
  6       HuggingFace local     FLAN-T5               No key needed
```

> **Zero downtime:** If Gemini quota is exceeded, the agent silently falls back — you always get a response.

</details>

---

## 🚀 Quick Start

### Prerequisites

```
Python 3.10+   Git   FFmpeg (optional, for video transcription)
```

### 1 · Clone & Install

```bash
git clone https://github.com/Misrilal-Sah/capstone-ai-code-review-and-correction-agent.git
cd capstone-ai-code-review-and-correction-agent

# Create virtual environment
python -m venv venv

# Activate  (Windows)
venv\Scripts\activate
# Activate  (Linux / macOS)
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 2 · Configure API Keys

Create a `.env` file in the project root:

```env
# ── Primary LLM ────────────────────────────────────────────
# Google AI Studio → https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_key

# ── Fast Fallback (Free) ────────────────────────────────────
# Groq Console → https://console.groq.com/
GROQ_API_KEY=your_groq_key

# ── Optional Free Fallbacks ─────────────────────────────────
# OpenRouter → https://openrouter.ai/
OPENROUTER_KEY_1=your_openrouter_key

# ── GitHub PR Review ────────────────────────────────────────
# GitHub → Settings > Developer settings > Personal access tokens
GITHUB_TOKEN=your_github_pat
```

> **Minimum viable setup:** Only `GEMINI_API_KEY` or `GROQ_API_KEY` is required. FLAN-T5 works with no keys at all.

### 3 · Index the Knowledge Base

```bash
# Index all PDFs in the default data folder (run once)
python code_review_main.py index --data-dir ./Data/python
```

```
  📂  Scanning ./Data/python ... 22 PDFs + 2 transcripts found
  ⚙️   Chunking documents ......... 7,124 chunks
  🔢  Generating embeddings ..... all-MiniLM-L6-v2
  💾  Persisting to ChromaDB .... ✓ done
```

> **Extend the knowledge base:** Drop extra PDFs or `.mp4` videos anywhere under `./Data/` and re-run the index command.

---

## 🖥️ CLI Reference

### `code_review_main.py`

```bash
# ── File / Folder ────────────────────────────────────────────
python code_review_main.py review <path>          # Single file or folder
python code_review_main.py review ./src/ --output ./reports

# ── Git Integration ──────────────────────────────────────────
python code_review_main.py review-changes         # Uncommitted tracked files
python code_review_main.py review-changes --staged # Staged files (git add first)
python code_review_main.py review-commit <hash>   # Specific commit

# ── GitHub Pull Request ──────────────────────────────────────
python code_review_main.py review-pr 42 --repo owner/repo

# ── Knowledge Base ───────────────────────────────────────────
python code_review_main.py index --data-dir ./Data/python
```

### `rag_main.py`

```bash
# ── Interactive Chat ─────────────────────────────────────────
python rag_main.py chat                           # REPL with history

# ── Single Question ──────────────────────────────────────────
python rag_main.py ask "What are SOLID principles?"
python rag_main.py ask "Why use type hints?" --verbose --show-reasoning

# ── Evaluation Run ───────────────────────────────────────────
python rag_main.py evaluate                       # Runs built-in test suite
```

---

## 📁 Project Structure

```
capstone-ai-code-review-and-correction-agent/
│
├── 🔍 code_review/                    Code Review Agent package
│   ├── agent.py                       Core agentic loop (7-step pipeline)
│   ├── llm_provider.py                Multi-LLM fallback chain
│   ├── static_analyzer.py             AST-based analysis · 24 rules
│   ├── tools.py                       file_reader, sandbox_validator, …
│   ├── reflection.py                  Self-reflection with confidence scoring
│   ├── evaluator.py                   Review quality metrics
│   └── git_integration.py             Git diff + GitHub PR via API
│
├── 🤖 rag_agent/                      RAG Chatbot Agent package
│   ├── agent.py                       Agentic loop with 5-step reasoning
│   ├── tools.py                       knowledge_search, clarify_question, …
│   ├── reflection.py                  Confidence-based reflection
│   └── evaluator.py                   Relevance · Groundedness · Clarity · Completeness
│
├── 🔗 rag_chatbot/                    Shared RAG infrastructure
│   ├── chatbot.py                     Main orchestrator
│   ├── pdf_loader.py                  PyMuPDF document ingestion
│   ├── audio_transcriber.py           Whisper MP4 → text
│   ├── chunker.py                     LangChain recursive splitting
│   ├── embedder.py                    SentenceTransformers (MiniLM)
│   ├── vector_store.py                ChromaDB persistence layer
│   ├── retriever.py                   Semantic k-NN search
│   └── generator.py                   LLM response generation
│
├── 📂 Data/                           Knowledge base root
│   ├── *.pdf                          GenAI / RAG lecture PDFs
│   ├── *.mp4                          Video lectures (auto-transcribed)
│   └── python/                        22 Python best-practice PDFs
│       ├── Clean-Python.pdf
│       ├── Static_analysis_of_Python_code.pdf
│       └── …
│
├── 🧪 samples/python/                 Test inputs for code review
│   ├── bad_code_smells.py
│   ├── bad_code_security.py
│   └── bad_code_exceptions.py
│
├── code_review_main.py                CLI entry-point for Code Review Agent
├── rag_main.py                        CLI entry-point for RAG Chatbot Agent
├── test_rag_agent.py                  Automated agent test harness
├── Rag_chatbot_answer.txt             Sample test output (7,124-chunk KB)
├── architecture.mmd                   Mermaid system diagram
└── requirements.txt                   Pinned dependencies
```

---

## 📊 Evaluation & Metrics

### Code Review Agent

| Metric | What It Measures |
|---|---|
| **Issues Found** | Total AST / LLM violations detected |
| **Confidence Score** | 0–100 % certainty of review completeness |
| **Overall Score** | 0–10 code quality rating |
| **Validation Status** | Pass / Fail from Black + Pylint + compile() |
| **Audit Hash** | SHA-256 of the reviewed file (immutable log) |

### RAG Chatbot Agent

| Metric | What It Measures |
|---|---|
| **Relevance** | Semantic match of answer to question intent |
| **Groundedness** | Claims traceable to retrieved chunks |
| **Clarity** | Readability, structure, formatting |
| **Completeness** | Coverage of all question facets |
| **Grade** | Composite letter grade A → F |

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| **Primary LLM** | ![Gemini](https://img.shields.io/badge/Gemini_2.5_Pro-4285F4?style=flat-square&logo=google) |
| **Fast LLM** | ![Groq](https://img.shields.io/badge/Groq_llama--3.1--8b-F54E42?style=flat-square) |
| **Local LLM** | ![HuggingFace](https://img.shields.io/badge/FLAN--T5_Local-FFD21E?style=flat-square&logo=huggingface&logoColor=black) |
| **Embeddings** | ![SentenceTransformers](https://img.shields.io/badge/SentenceTransformers_MiniLM-FF6B35?style=flat-square) |
| **Vector DB** | ![ChromaDB](https://img.shields.io/badge/ChromaDB_7124_chunks-1C3C3C?style=flat-square) |
| **PDF Processing** | ![PyMuPDF](https://img.shields.io/badge/PyMuPDF-3776AB?style=flat-square&logo=python&logoColor=white) |
| **Audio / Video** | ![Whisper](https://img.shields.io/badge/OpenAI_Whisper-412991?style=flat-square&logo=openai&logoColor=white) |
| **Static Analysis** | ![AST](https://img.shields.io/badge/Python_AST_·_Pylint_·_Black-3776AB?style=flat-square&logo=python&logoColor=white) |
| **RAG Framework** | ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square) |
| **Git Integration** | ![GitHub](https://img.shields.io/badge/GitHub_API-181717?style=flat-square&logo=github) |

</div>

---

## 💡 Optional: Extend the Knowledge Base

You can enrich the RAG knowledge base with additional videos:

| Resource | Topic |
|---|---|
| [Error Handling Techniques](https://youtu.be/YA0Wq1rcs6U) | Advanced Python exception patterns |
| [Python Full Course 2025](https://youtu.be/K5KVEU3aaeQ) | Comprehensive language reference |
| [Functional Programming in Python](https://youtu.be/PBc4flRmdBY) | FP patterns and best practices |

```bash
# Place .mp4 files in ./Data/python/ then re-index
python code_review_main.py index --data-dir ./Data/python
```

---

<div align="center">

---

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   Built with  ♥  by  Misrilal Sah                               ║
║                                                                  ║
║   "Good code is its own best documentation."                    ║
║                              — Steve McConnell                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

[![GitHub](https://img.shields.io/badge/@Misrilal--Sah-181717?style=for-the-badge&logo=github)](https://github.com/Misrilal-Sah)

*Built as a capstone project for AI Academy · Powered by open-source LLMs & HuggingFace*

</div>
