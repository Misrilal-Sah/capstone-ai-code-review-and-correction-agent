# AI Agentic System - Code Review & RAG Chatbot

An intelligent, autonomous AI agent system featuring **two specialized agents**:
1. **Code Review Agent** - Comprehensive Python code analysis with fixes
2. **RAG Chatbot Agent** - General-purpose Q&A with knowledge base retrieval

Both agents use RAG (Retrieval-Augmented Generation), multi-LLM fallback chains, and self-reflection capabilities.

## 🎯 Project Overview

This project implements an **AI Agentic System** that demonstrates:

- **Data Preparation & Contextualization** - Multi-modal data loading (PDFs, videos)
- **RAG Pipeline Design** - Semantic search with ChromaDB and embeddings
- **Reasoning & Reflection** - Self-evaluation with confidence scoring
- **Tool-Calling Mechanisms** - Modular tools for actions (search, analyze, validate)
- **Evaluation Metrics** - Quality measurement (relevance, groundedness, clarity)

> **Two Agents, One System:**
> - `python rag_main.py` → General-purpose RAG Chatbot Agent
> - `python code_review_main.py` → Specialized Code Review Agent

---

## 🏗️ Architecture

This project has **two specialized agents** that share a common RAG infrastructure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT                                     │
│   ┌─────────────────────────┐         ┌───────────────────────────────────┐│
│   │   Question / Query      │         │  Code File / Folder / Git / PR    ││
│   └───────────┬─────────────┘         └─────────────────┬─────────────────┘│
└───────────────┼─────────────────────────────────────────┼───────────────────┘
                │                                         │
                ▼                                         ▼
┌───────────────────────────────┐     ┌───────────────────────────────────────┐
│   🤖 RAG CHATBOT AGENT        │     │      🔍 CODE REVIEW AGENT             │
│   (rag_main.py)               │     │      (code_review_main.py)            │
│                               │     │                                       │
│  ┌──────────────────────────┐ │     │  ┌─────────────────────────────────┐  │
│  │ Tools:                   │ │     │  │ Tools:                          │  │
│  │ • knowledge_search       │ │     │  │ • file_reader                   │  │
│  │ • clarify_question       │ │     │  │ • static_analysis_helper        │  │
│  │ • markdown_writer        │ │     │  │ • markdown_writer               │  │
│  │ • provide_sources        │ │     │  │ • sandbox_validator             │  │
│  └──────────────────────────┘ │     │  └─────────────────────────────────┘  │
│                               │     │                                       │
│  ┌──────────────────────────┐ │     │  ┌─────────────────────────────────┐  │
│  │ Self-Reflection          │ │     │  │ Self-Reflection (3 iterations)  │  │
│  │ + Confidence Scoring     │ │     │  │ + Sandbox Validation            │  │
│  └──────────────────────────┘ │     │  └─────────────────────────────────┘  │
│                               │     │                                       │
│  ┌──────────────────────────┐ │     │  ┌─────────────────────────────────┐  │
│  │ Evaluation Metrics:      │ │     │  │ Static Analysis:                │  │
│  │ • Relevance              │ │     │  │ • AST Parsing (24 rules)        │  │
│  │ • Groundedness           │ │     │  │ • Pylint, Black                 │  │
│  │ • Clarity                │ │     │  │ • Syntax Validation             │  │
│  │ • Completeness           │ │     │  └─────────────────────────────────┘  │
│  └──────────────────────────┘ │     │                                       │
└───────────────┬───────────────┘     └─────────────────┬─────────────────────┘
                │                                       │
                └───────────────────┬───────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🔗 SHARED INFRASTRUCTURE                             │
│  ┌────────────────────────────┐    ┌────────────────────────────────────┐  │
│  │ 🧠 Multi-LLM Fallback:     │    │ 📚 RAG Pipeline:                   │  │
│  │ Gemini → Groq → Flash →   │    │ PDF Loader → Chunker → Embedder → │  │
│  │ OpenRouter → FLAN-T5      │    │ ChromaDB (7,124 chunks)            │  │
│  └────────────────────────────┘    └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              📤 OUTPUT                                      │
│   ┌─────────────────────────┐         ┌───────────────────────────────────┐│
│   │ Answer + Sources +      │         │ codereview.md + corrected_*.py    ││
│   │ Confidence + Grade      │         │ + audit_log.json                  ││
│   └─────────────────────────┘         └───────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

See `architecture.mmd` for a detailed Mermaid diagram.

---

## ✨ Features

### 1. Multi-Source Code Review
- **Single file review**: `python code_review_main.py review file.py`
- **Folder review**: `python code_review_main.py review ./src/`
- **Git uncommitted changes**: `python code_review_main.py review-changes`
- **Specific commit**: `python code_review_main.py review-commit <hash>`
- **GitHub Pull Request**: `python code_review_main.py review-pr <PR#> --repo owner/repo`

### 2. RAG-Powered Knowledge Base
- **22 PDF documents** on Python best practices, design patterns, security, RAG concepts
- **2 Video transcripts** (Whisper-transcribed) on RAG and GenAI databases
- **7,124 knowledge chunks** indexed in ChromaDB
- **Semantic search** using `all-MiniLM-L6-v2` embeddings
- **Recursive indexing** - automatically finds all PDFs in subdirectories

### 3. Multi-LLM Fallback Chain
Priority order with automatic fallback:
1. **Gemini 2.5 Pro** → Best quality
2. **Groq (llama-3.1-8b)** → Fast, 90%+ confidence
3. **Gemini 2.5 Flash** → Backup
4. **OpenRouter (Kat Coder Pro)** → Free tier
5. **OpenRouter (Nova 2 Lite)** → Free tier
6. **FLAN-T5 (Local)** → No API needed

### 4. Self-Reflection & Reasoning
- Up to **3 reflection iterations** to improve review quality
- **Confidence scoring** (0-100%) for each review
- Automatic refinement if confidence < 70%

### 5. Sandbox Validation
- **Syntax check** with Python's `compile()`
- **Black formatting** check
- **Pylint** quality score
- Only presents validated fixes

### 6. Tool-Calling Architecture
**Code Review Agent Tools:**
- `file_reader` → Read code files
- `static_analysis_helper` → AST-based analysis
- `markdown_writer` → Generate reports
- `sandbox_validator` → Validate fixes

**RAG Chatbot Agent Tools:**
- `knowledge_search` → Search RAG knowledge base
- `clarify_question` → Rephrase ambiguous questions
- `summarize_context` → Summarize long contexts
- `provide_sources` → Format source citations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- FFmpeg (for video transcription)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/Misrilal-Sah/capstone-ai-code-review-and-correction-agent.git
cd capstone-ai-code-review-and-correction-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configure API Keys

Create a `.env` file:

```env
# Google Gemini (Primary)(google studio)
GEMINI_API_KEY=your_gemini_key

# Groq (Backup - Free)(https://console.groq.com/)
GROQ_API_KEY=your_groq_key

# OpenRouter (Optional - Free)
OPENROUTER_KEY_1=your_openrouter_key

# GitHub (For PR review)
GITHUB_TOKEN=your_github_pat
```

### Index Knowledge Base (First Run)

The knowledge base includes **20 PDF documents** on Python best practices. You can optionally download videos for additional knowledge:

**Optional Video Downloads:**
- [Error Handling Techniques](https://youtu.be/YA0Wq1rcs6U?si=dPTCqGRKaE3YI_Xj)
- [Python Full Course 2025](https://youtu.be/K5KVEU3aaeQ?si=racmqfXbB-FKj7KD)
- [Functional Programming in Python](https://youtu.be/PBc4flRmdBY?si=Q7xo7h1sSl3dQjbf)

Place downloaded videos in `./Data/python/` folder.

```bash
# Index the knowledge base
python code_review_main.py index --data-dir ./Data/python
```

> **💡 Extend Knowledge Base:** You can add more PDFs or videos to the `Data/` folder (including subdirectories like `Data/python/`). The RAG system will automatically index any new documents when you run the `index` command. We tested with 22 PDFs and 2 videos (7,124 chunks indexed).

### Run Code Review

```bash
# Review a single file
python code_review_main.py review ./samples/python/bad_code_smells.py

# Review entire folder
python code_review_main.py review ./samples/python

# Review uncommitted changes (modified tracked files)
python code_review_main.py review-changes

# Review staged changes (new or modified files - use git add first)
python code_review_main.py review-changes --staged

# Review a specific commit
python code_review_main.py review-commit abc123

# Review a GitHub PR
python code_review_main.py review-pr 42 --repo owner/repo
```

> **💡 Tip:** For new (untracked) files, use `git add <file>` first, then run `review-changes --staged`.

### Run RAG Chatbot Agent

```bash
# Interactive chat with reasoning and reflection
python rag_main.py chat

# Ask a single question
python rag_main.py ask "What are best practices for RAG?"

# Run evaluation on test questions
python rag_main.py evaluate

# Show reasoning steps
python rag_main.py ask "Why is hybrid search better?" --verbose --show-reasoning
```

**Example Output:**
```
============================================================
Question: What are the production 'Do's' for RAG?
============================================================

[Step 1] Reasoning about the question...
[Step 2] Searching knowledge base...
  Found 5 relevant chunks
[Step 3] Generating answer...
[Step 4] Self-reflecting on response...
  Confidence: 0.85
[Step 5] Evaluating response quality...
  Grade: B (score: 0.82)

Answer:
The production Do's for RAG include:
1. Use hybrid search combining vector and keyword search
2. Implement proper chunking strategies
3. Add metadata filtering for better relevance
...

Sources: RAG_Best_Practices.pdf, Production_ML.pdf
============================================================
✓ Response generated (confidence: 0.85)
============================================================
```

---

## 📁 Project Structure

```
├── code_review/                 # Code Review Agent package
│   ├── agent.py                 # Core agent with agentic loop
│   ├── llm_provider.py          # Multi-LLM fallback chain
│   ├── static_analyzer.py       # AST-based analysis (24 rules)
│   ├── tools.py                 # Tool functions
│   ├── reflection.py            # Self-reflection layer
│   ├── evaluator.py             # Review evaluation metrics
│   └── git_integration.py       # Git/GitHub integration
│
├── rag_agent/                   # RAG Chatbot Agent package (NEW)
│   ├── agent.py                 # Agentic loop with reasoning
│   ├── tools.py                 # Tool functions (search, clarify, summarize)
│   ├── reflection.py            # Self-reflection & confidence scoring
│   └── evaluator.py             # Response quality metrics
│
├── rag_chatbot/                 # Base RAG pipeline
│   ├── chatbot.py               # Main RAG chatbot
│   ├── pdf_loader.py            # PDF processing
│   ├── audio_transcriber.py     # Whisper transcription
│   ├── chunker.py               # Text chunking
│   ├── embedder.py              # Embeddings
│   ├── vector_store.py          # ChromaDB storage
│   ├── retriever.py             # Semantic search
│   └── generator.py             # LLM response
│
├── Data/                        # Knowledge base root
│   ├── *.pdf                    # GenAI lecture PDFs
│   ├── *.mp4                    # Video lectures (auto-transcribed)
│   └── python/                  # Python-specific PDFs (20 files)
│       ├── Clean-Python.pdf
│       ├── Static_analysis_of_Python_code.pdf
│       └── ...                  # Design patterns, security, exceptions
│
├── rag_main.py                  # CLI for RAG Chatbot Agent
├── code_review_main.py          # CLI for Code Review Agent
├── test_rag_agent.py            # Test script for RAG Agent
├── Rag_chatbot_answer.txt       # Sample output from RAG Agent test
├── architecture.mmd             # System architecture diagram (Mermaid)
└── requirements.txt             # Dependencies
```

> **Two Entry Points:** Use `rag_main.py` for general Q&A and `code_review_main.py` for code analysis.

---

## 📊 Evaluation Metrics

The agent calculates:

| Metric | Description |
|--------|-------------|
| **Issues Found** | Count of detected problems |
| **Confidence Score** | 0-100% certainty of review quality |
| **Overall Score** | 0-10 code quality rating |
| **Validation Status** | Pass/Fail for suggested fixes |

---

## 🛠️ Technologies Used

| Category | Technology |
|----------|------------|
| **LLMs** | Gemini 2.5 Pro/Flash, Groq, OpenRouter, FLAN-T5 |
| **Embeddings** | SentenceTransformers (all-MiniLM-L6-v2) |
| **Vector DB** | ChromaDB |
| **PDF Processing** | PyMuPDF |
| **Audio Transcription** | OpenAI Whisper |
| **Static Analysis** | Python AST, Pylint, Black |
| **Frameworks** | LangChain |

---

## 📖 Example Output

```
============================================================
Reviewing: samples/python/bad_code_smells.py
============================================================

[1/7] Reading file...
[2/7] Running static analysis...
  Found 33 static analysis issues
[3/7] Retrieving best practices...
[4/7] Generating code review...
  ✓ Using Groq llama-3.1-8b-instant
[5/7] Running self-reflection...
  Reflection iteration 1: confidence = 0.85
[6/7] Validating fixes...
  ✓ Suggested fix passed validation
[7/7] Generating outputs...
  ✓ Report saved: codereview.md
  ✓ Corrected code saved: corrected_bad_code_smells.py

============================================================
Review complete! Confidence: 90.0%
============================================================
```

---

## 👤 Author

**Misrilal Sah**

- GitHub: [@Misrilal-Sah](https://github.com/Misrilal-Sah)

---

## 🙏 Acknowledgments

- AI Academy for the assignment
- HuggingFace for open-source models
