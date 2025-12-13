# AI Code Review and Correction Agent

An intelligent, autonomous AI agent that performs comprehensive code reviews using RAG (Retrieval-Augmented Generation), multi-LLM fallback chains, and self-reflection capabilities.

## 🎯 Project Overview

This project implements an **AI Agentic System** for **Python code review** that:

- **Analyzes Python code** for bugs, security issues, code smells, and best practice violations
- **Uses RAG** to retrieve relevant knowledge from PDFs and video transcripts
- **Generates corrected code** with proper fixes
- **Self-reflects** on its own outputs to improve quality
- **Validates fixes** in a sandbox before presenting them

> **⚠️ Python Only:** This agent currently supports **Python files only** (`.py`). When using `review-commit`, `review-changes`, or `review-pr`, non-Python files are automatically skipped.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                  │
│           (Code file/folder/commit/PR/git changes)                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CODE REVIEW AGENT                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │ Static Analyzer│  │  RAG Retriever │  │  LLM Provider  │        │
│  │  (AST + Rules) │  │ (ChromaDB+PDF) │  │(Gemini→Groq→..)│        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
│           │                   │                   │                 │
│           └───────────────────┼───────────────────┘                 │
│                               ▼                                     │
│                    ┌──────────────────────┐                         │
│                    │  Review Generation   │                         │
│                    │  + Code Correction   │                         │
│                    └──────────────────────┘                         │
│                               │                                     │
│                               ▼                                     │
│                    ┌──────────────────────┐                         │
│                    │  Self-Reflection     │                         │
│                    │  (3 iterations max)  │                         │
│                    └──────────────────────┘                         │
│                               │                                     │
│                               ▼                                     │
│                    ┌──────────────────────┐                         │
│                    │  Sandbox Validator   │                         │
│                    │  (syntax/black/lint) │                         │
│                    └──────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           OUTPUT                                    │
│     codereview.md  |  corrected_*.py  |  audit_log.json            │
└─────────────────────────────────────────────────────────────────────┘
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
- **20 PDF documents** on Python best practices, design patterns, security
- **3 Video transcripts** (Whisper-transcribed) on error handling, FP, advanced Python
- **7,166 knowledge chunks** indexed in ChromaDB
- **Semantic search** using `all-MiniLM-L6-v2` embeddings

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
Modular tools following agentic design:
- `file_reader` → Read code files
- `static_analysis_helper` → AST-based analysis
- `markdown_writer` → Generate reports
- `inline_comment_generator` → Git-style comments
- `sandbox_validator` → Validate fixes

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

> **💡 Extend Knowledge Base:** You can add more PDFs or videos to the `Data/python/` folder. The RAG system will automatically index any new documents when you run the `index` command. We tested with 20+ PDFs and 3 videos (7,166 chunks indexed).

### Run Code Review

```bash
# Review a single file
python code_review_main.py review ./samples/python/bad_code_smells.py

# Review entire folder
python code_review_main.py review ./src/ --output-dir ./reviews

# Review uncommitted changes
python code_review_main.py review-changes

# Review a specific commit
python code_review_main.py review-commit abc123

# Review a GitHub PR
python code_review_main.py review-pr 42 --repo owner/repo
```

---

## 📁 Project Structure

```
├── code_review/                 # Main agent package
│   ├── __init__.py
│   ├── agent.py                 # Core agent with agentic loop
│   ├── llm_provider.py          # Multi-LLM fallback chain
│   ├── static_analyzer.py       # AST-based analysis (24 rules)
│   ├── tools.py                 # Tool functions
│   ├── reflection.py            # Self-reflection layer
│   ├── evaluator.py             # Review evaluation metrics
│   └── git_integration.py       # Git/GitHub integration
│
├── rag_chatbot/                 # RAG pipeline
│   ├── chatbot.py               # Main RAG chatbot
│   ├── pdf_loader.py            # PDF processing
│   ├── audio_transcriber.py     # Whisper transcription
│   ├── chunker.py               # Text chunking
│   ├── embedder.py              # Embeddings
│   ├── vector_store.py          # ChromaDB storage
│   ├── retriever.py             # Semantic search
│   └── generator.py             # LLM response
│
├── Data/python/                 # Knowledge base documents
│   ├── *.pdf                    # 20 Python best practice PDFs
│   └── *.mp4                    # 3 educational videos
│
├── samples/python/              # Sample bad code for testing
│   ├── bad_code_smells.py
│   ├── bad_code_security.py
│   └── bad_code_exceptions.py
│
├── code_review_output/          # Generated outputs
│   ├── codereview.md            # Combined review report
│   ├── corrected_*.py           # Fixed code files
│   └── audit_log.json           # Audit trail
│
├── code_review_main.py          # CLI entry point
├── requirements.txt             # Dependencies
├── architecture.mmd             # Mermaid architecture diagram
├── README.md                    # This file
│
├── test_chatbot.py              # (HW4) RAG chatbot test script
└── answer_log.txt               # (HW4) Test output log
```

> **Note:** `test_chatbot.py` and `answer_log.txt` are from a previous homework (HW4) for RAG Chatbot development. They use the `Data/` folder for knowledge base documents.

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
- Anthropic, Google, Groq for LLM APIs
- HuggingFace for open-source models
