# AUTOSAR HLD Document Analysis Assistant - Codebase

This module contains the implementation for the fully offline, RAG-based AUTOSAR High-Level Design (HLD) Document Analysis Assistant.

## Prerequisites
- Python 3.10+ (Recommended: Python 3.11)
- Ollama installed locally for local LLM inference
- System RAM: 12 GB+

## Setup Instructions

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### 2. Install Pinned Dependencies
```bash
pip install -r requirements.txt
```

### 3. Local Model Pull (Ollama)
Ensure Ollama server is running, then pull the local LLM:
```bash
ollama pull qwen2.5:3b
```
*(For machines with higher VRAM/RAM, `qwen2.5:7b` can also be used).*

Embeddings (`BAAI/bge-small-en-v1.5`) are managed via `sentence-transformers` and stored locally in ChromaDB.

## Module Overview
- `generate_synthetic_data.py`: Script to generate synthetic multi-page AUTOSAR HLD PDFs (v1 and v2) and defect ground truths.
- `ingest.py`: PDF document parser and text/table extractor.
- `chunk_embed.py`: Section-aware chunking and BGE embeddings generator stored in ChromaDB.
- `rag.py`: RAG query orchestration with citation verification and confidence scoring.
- `extract_entities.py`: Deterministic and LLM-assisted component/interface/signal extraction.
- `compare.py`: Deterministic HLD v1 vs v2 revision inconsistency detector and architectural report generator.
- `app.py`: Streamlit-based interactive web interface.
- `evaluate.py`: Evaluation harness computing Hit@k, MRR, groundedness, and defect detection recall.
