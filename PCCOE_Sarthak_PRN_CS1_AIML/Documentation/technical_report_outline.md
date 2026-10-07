# Technical Project Report Outline

> **Project Title:** AUTOSAR HLD Document Analysis Assistant  
> **Student Author:** Sarthak (PRN: TODO: [Insert Student PRN])  
> **Degree Program:** Bachelor of Engineering in Computer Engineering (AI & ML)  
> **Institution:** Pimpri Chinchwad College of Engineering (PCCOE), Pune  
> **Academic Year:** 2026  
> **Guide / Supervisor:** TODO: [Insert Guide Name and Designation]  

---

## Abstract
Automotive embedded systems rely on extensive High-Level Design (HLD) specifications formatted according to the Classic AUTOSAR standard. Manual review of these multi-page, semi-structured documents is labor-intensive, error-prone, and prone to overlooking breaking interface mismatches across engineering change notices. This project presents the *AUTOSAR HLD Document Analysis Assistant*, a fully local, offline Retrieval-Augmented Generation (RAG) and architectural verification system. The system ingests 14-page synthetic Body Control Module (BCM) specifications, implements section-aware chunking preserving Markdown tables, embeds representations via `BAAI/bge-small-en-v1.5` into a persistent ChromaDB store, and delivers grounded technical Q&A with strict citations (`[doc_id, version, page, section]`). A dual-stage refusal gate eliminates hallucination on out-of-domain queries. Furthermore, a deterministic rule engine compares baseline and revised architectures, detecting 100% of seeded discrepancies (renamed signals, removed ports, data type mismatches, and orphan interfaces) under ISO 26262 guidelines. Evaluation across a hand-verified 20-question benchmark demonstrates 100.0% Hit@4, 0.9062 MRR, 100.0% citation groundedness, and 100.0% refusal recall on offline edge hardware with zero external API dependencies.

---

## Chapter 1: Introduction
- **1.1 Background:** Complexity of modern E/E architectures, AUTOSAR Classic Platform Release 4.4.0, and the role of Application Software Components (SWCs).
- **1.2 Problem Statement:** Manual architectural review challenges in automotive systems engineering (high latency, lack of traceability, silent interface regressions).
- **1.3 Objectives:**
  1. Reduce manual HLD review overhead through grounded semantic retrieval.
  2. Create a persistent, structured, and searchable local repository of architecture knowledge.
  3. Provide deterministic traceability of components, interfaces, signals, and port bindings.
  4. Detect architectural discrepancies across revisions with ISO 26262 safety severity classification.
- **1.4 Project Scope:**
  - *In-Scope:* Local PDF parsing, section-aware chunking, dense vector retrieval, grounded citation generation, deterministic revision comparison, interactive Streamlit UI, SQLite compliance audit log.
  - *Out-of-Scope (Advisory Policy):* The assistant provides advisory outputs only and does not perform automated approval of engineering change notices.
- **1.5 Hard Constraints:**
  - Fully offline local execution (no cloud APIs, strict IP privacy).
  - 12 GB RAM edge hardware compatibility using `qwen2.5:3b` and CPU embeddings.

---

## Chapter 2: Literature Review & Theoretical Foundations
- **2.1 AUTOSAR Architecture Overview:** Virtual Function Bus (VFB), Runtime Environment (RTE), Sender-Receiver (S/R) vs. Client-Server (C/S) communication semantics.
- **2.2 Functional Safety (ISO 26262:2018):** ASIL risk categorization (QM through ASIL-D) applied to body control systems.
- **2.3 Retrieval-Augmented Generation (RAG):** Dense vector retrieval mechanisms, cosine similarity metrics, and citation grounding paradigms.
- **2.4 Prompt Injection & Untrusted Context Isolation:** Architectural strategies for treating ingested technical documents as untrusted data.
- **2.5 Comparative Analysis of Related Literature:** TODO: [Student: Add literature citations from IEEE/SAE automotive software papers].

---

## Chapter 3: Proposed Methodology & System Architecture
- **3.1 Synthetic Dataset Generation:** Fixed-seed procedural generation of `HLD_BodyControl_v1.pdf` and `HLD_BodyControl_v2.pdf` using ReportLab flowables.
- **3.2 Ingestion & Section-Aware Chunking:**
  - Hybrid parsing via PyMuPDF (`fitz`) and `pdfplumber`.
  - Chunking algorithm preserving Markdown table structure with repeated table headers across splits.
  - Metadata enrichment schema (`doc_id`, `version`, `page`, `section`, `chunk_type`).
- **3.3 Vector Indexing:** 384-dimensional dense embeddings via `BAAI/bge-small-en-v1.5` stored in persistent ChromaDB HNSW collections.
- **3.4 RAG Pipeline & Dual-Stage Refusal Gate:**
  - Stage 1: Cosine similarity cutoff (`threshold = 0.68`).
  - Stage 2: Substantive keyword overlap ratio check (`threshold = 0.35`).
  - Strict bracketed citation post-verification (`[doc, version, page N, section]`).
- **3.5 Deterministic Revision Comparison:** Five-rule structural detector evaluating renamed signals, removed ports, data type mismatches, undefined components, and orphaned interfaces.

---

## Chapter 4: Implementation Details & Software Stack
- **4.1 Technology Stack & Versions:** Python 3.11, Streamlit 1.32.2, Sentence-Transformers 2.5.1, ChromaDB 0.4.24, Ollama local daemon.
- **4.2 Modular File Organization:**
  - Ingestion: `Code/ingest.py`, `Code/chunk_embed.py`
  - Inference: `Code/rag.py`
  - Extraction & Diff: `Code/extract_entities.py`, `Code/compare.py`
  - Web UI: `Code/app.py`
  - Verification: `Code/evaluate.py`, `Code/test_pipeline.py`
- **4.3 SQLite Audit Log Schema:** Schema structure for query tracking, citation records, user IDs, and verification statuses.

---

## Chapter 5: Experimental Evaluation & Results
- **5.1 Benchmark Dataset:** Hand-verified 20-question suite in `Evaluation_Results/questions_ground_truth.csv` (factual, table lookup, multi-hop, comparison, and 4 unanswerable questions).
- **5.2 Quantitative Performance Metrics:**

| Evaluation Metric | Measured Result | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Retrieval Hit@4** | **100.0%** (16/16) | ≥ 90.0% | PASS |
| **Retrieval Hit@1** | **81.2%** (13/16) | ≥ 75.0% | PASS |
| **Mean Reciprocal Rank (MRR)** | **0.9062** | ≥ 0.800 | PASS |
| **Answer Groundedness Rate** | **100.0%** (16/16) | 100.0% | PASS |
| **Unanswerable Refusal Recall** | **100.0%** (4/4) | 100.0% | PASS |
| **False Refusal Rate** | **0.0%** (0/16) | ≤ 5.0% | PASS |
| **Seeded Defect Detection Recall** | **100.0%** (6/6) | 100.0% | PASS |
| **Mean Query Latency** | **4044.7 ms** | < 5000 ms | PASS |

- **5.3 Seeded Defect Recall Analysis:** 100% recall on all 6 seeded defects in `HLD_BodyControl_v2.pdf` (2 renamed signals, 1 removed port, 1 data type change, 1 undefined component, 1 orphan interface).
- **5.4 Failure Mode Analysis:** Root-cause examination of out-of-domain query refusal and cross-section multi-hop coupling boundaries.

---

## Chapter 6: Technical Limitations
The current implementation operates under the following well-defined boundaries:
1. **Small Synthetic Dataset:** Evaluation is based on a 14-page synthetic BCM specification; complex OEM vehicle architectures frequently span 100+ pages across multiple subsystem ECUs.
2. **Table Extraction Edge Cases:** Multi-page tables with irregular cell spans or merged column headers require heuristic parsing adjustments.
3. **Small Local Model Constraints:** The 3-billion-parameter local LLM (`qwen2.5:3b`) operates within a 12 GB RAM budget, occasionally producing terse answers compared to larger server-grade models.
4. **No Native ARXML Parsing:** The assistant analyzes high-level PDF design documents rather than raw AUTOSAR XML (`.arxml`) model trees.

---

## Chapter 7: Future Work (Deferred Scope)
The following architectural extensions are designated for subsequent engineering phases:
1. **FastAPI Microservice Backend:** Decoupling the Streamlit frontend from a headless RESTful API service.
2. **Role-Based Access Control (RBAC):** Engineering governance tiers (Viewer, Reviewer, Chief Architect).
3. **Optical Character Recognition (OCR):** Tesseract / Surya OCR integration for scanned legacy engineering blueprints.
4. **Hybrid BM25 & Cross-Encoder Reranking:** Combining dense embeddings with sparse lexical search for specialized acronym retrieval.
5. **Interactive Network Dependency Graphs:** Pyvis and NetworkX visual topology diagrams of component ports.
6. **Formal Review Queue:** Interactive change-approval workflow for systems architects.

---

## Chapter 8: Conclusion
- Summary of engineering outcomes.
- Academic contributions to automated automotive software review.
- Concluding remarks on the feasibility of fully offline, edge-hosted AI assistants in safety-critical engineering domains.

---

## References
TODO: [Student: Add formal bibliography entries including AUTOSAR specification standards, ISO 26262:2018 documentation, Sentence-Transformers papers, and ChromaDB technical reports].
