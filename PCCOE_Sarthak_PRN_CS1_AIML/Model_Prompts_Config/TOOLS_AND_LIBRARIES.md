# Tools and Libraries Declaration

> **Project:** AUTOSAR HLD Document Analysis Assistant  
> **Institution:** Pimpri Chinchwad College of Engineering (PCCOE), Pune  
> **Department:** Computer Engineering / AI & ML Lab  
> **Academic Year:** 2026  

This document details all third-party libraries, runtime engines, and dependencies utilized in this project, complete with pinned versions, licensing terms, and technical rationale.

---

## 1. Core Document Processing & Generation

| Library / Tool | Pinned Version | License | Primary Role in Project | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | `3.11.x` | PSF | Core execution runtime | Stable async support, native typing, and optimal PyTorch/ChromaDB compatibility. |
| **ReportLab** | `4.1.0` | BSD | Synthetic PDF generator | Precision PDF flowable layout engine used to generate reproducible 14-page baseline and revised HLDs. |
| **fpdf2** | `2.7.8` | LGPLv3 | Auxiliary PDF generation | Lightweight alternative PDF generation utility for standalone tests. |
| **Pillow (PIL)** | `10.2.0` | HPND | Image processing | High-performance image rendering and canvas manipulation for ReportLab charts. |
| **PyMuPDF (`fitz`)** | `1.23.26` | AGPLv3 | Fast PDF text & layout extraction | High-speed C-based PDF text parser used in `Code/ingest.py` to extract page-indexed text blocks. |
| **pdfplumber** | `0.10.4` | MIT | Tabular layout parsing | High-fidelity table bounding box extraction engine that converts multi-column tables into clean Markdown rows. |

---

## 2. Representation Learning & Vector Database

| Library / Tool | Pinned Version | License | Primary Role in Project | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **sentence-transformers** | `2.5.1` | Apache 2.0 | Dense semantic embeddings | Hosts `BAAI/bge-small-en-v1.5` locally, producing 384-dimensional dense vectors without cloud connectivity. |
| **ChromaDB** | `0.4.24` | Apache 2.0 | Persistent vector database | Embedded SQLite + DuckDB backed HNSW vector index store with zero external server dependencies. |
| **NumPy** | `1.26.4` | BSD-3 | Numerical linear algebra | High-performance cosine dot-product calculations and fallback similarity matrices. |

---

## 3. Local Language Model Infrastructure

| Library / Tool | Pinned Version | License | Primary Role in Project | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Ollama** | `v0.1.32+` | MIT | Local LLM runtime daemon | High-performance quantized GGUF inference engine serving `qwen2.5:3b` and `qwen2.5:7b` over local port `11434`. |
| **ollama-python** | `0.2.1` | MIT | Python client wrapper | Lightweight non-blocking API interface connecting `Code/rag.py` to local Ollama daemon. |
| **httpx** | `0.27.0` | BSD-3 | Local HTTP client | Async HTTP transport for local REST queries with custom timeout configurations. |

---

## 4. Web Application & User Interface

| Library / Tool | Pinned Version | License | Primary Role in Project | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Streamlit** | `1.32.2` | Apache 2.0 | Interactive web application | Single-framework Python UI providing tabbed navigation, real-time Q&A, and interactive comparison tables. |
| **Pandas** | `2.2.1` | BSD-3 | Structured data processing | Tabular serialization and manipulation for CSV entity exports, audit logs, and metrics. |

---

## 5. Evaluation, Quality Assurance & Testing

| Library / Tool | Pinned Version | License | Primary Role in Project | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **scikit-learn** | `1.4.1.post1` | BSD-3 | Quantitative scoring & metrics | Standardized validation metrics, cosine similarity cross-verification, and statistical aggregation. |
| **matplotlib** | `3.8.3` | PSF | Metric visualization | Graph generation for retrieval accuracy curves, MRR comparisons, and latency distributions. |
| **PyYAML** | `6.0.1` | MIT | Configuration deserialization | Clean parsing of `Model_Prompts_Config/model_config.yaml`. |
| **pytest** | `8.1.1` | MIT | Automated unit test runner | Test suite execution for chunking boundaries, citation formatting, and deterministic diff detectors. |
| **tabulate** | `0.9.0` | MIT | Text formatting | Clean ASCII table generation for CLI logging and terminal outputs. |

---

## 6. Embedded Database & Audit Log

| Library / Tool | Version | License | Primary Role in Project | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **SQLite3** | Native Python | Public Domain | Compliance audit log storage | Embedded transactional SQL storage in `Code/rag_audit_log.db` tracking every query, citation, and verification status. |

---

*Verified compliant with PCCOE Academic Guidelines and Open-Source Software Licensing Policies.*
