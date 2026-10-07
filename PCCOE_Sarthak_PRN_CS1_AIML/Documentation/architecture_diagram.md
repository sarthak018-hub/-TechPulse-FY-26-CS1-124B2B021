# AUTOSAR HLD Document Analysis Assistant: Architecture Specification

> **System Architecture & Dataflow Specification**  
> **Target Environment:** 100% Local / Offline Edge Execution (12 GB RAM, NVIDIA GeForce MX330 / CPU)  
> **Primary LLM:** Ollama `qwen2.5:3b` | **Dense Embeddings:** `BAAI/bge-small-en-v1.5`  

---

## 1. End-to-End System Architecture

The following diagram illustrates the interaction between the Streamlit user interface, the RAG orchestration pipeline, local vector/relational databases, and the offline inference components:

```mermaid
graph TB
    subgraph UI ["Presentation Layer (Streamlit Web UI - Port 8501)"]
        UI_QA["Tab 1: Q&A Assistant<br/>(Confidence Badge & Expandable Sources)"]
        UI_ING["Tab 2: Document Ingestion<br/>(Version Label & File Validator)"]
        UI_ENT["Tab 3: Entity Explorer<br/>(SWCs, Interfaces, Signals, Ports)"]
        UI_CMP["Tab 4: Revision Comparison<br/>(v1 vs v2 Inconsistency Diff Matrix)"]
        UI_EXP["Tab 5: Export Center<br/>(JSON & CSV Architecture Catalogs)"]
        UI_AUD["Tab 6: Compliance Audit Log<br/>(Full Query & Citation Traceability)"]
        UI_BAN["Advisory Warning Banner<br/>'AI-assisted output. Requires engineer review.'"]
    end

    subgraph ORCH ["RAG Orchestration & Verification Engine (Code/rag.py)"]
        INJ_DEF["Prompt Injection Defense<br/>(Context vs Instruction Separation)"]
        RET_ENG["Similarity Search Retriever<br/>(Top-k=4, Version Filter)"]
        REF_GATE["Dual-Stage Refusal Gate<br/>(Cosine Threshold < 0.68 + Keyword Overlap < 35%)"]
        LLM_CALL["Local Inference Handler<br/>(Temperature 0.1, Seed 42)"]
        EXT_FALL["Deterministic Extractive Fallback<br/>(Sentence-Level Semantic Grounding)"]
        VAL_CHK["Citation & Groundedness Post-Check<br/>(Validates [doc, ver, page, sec])"]
    end

    subgraph STORAGE ["Local Persistence Layer (Zero Cloud Connectivity)"]
        CHROMA[("ChromaDB Persistent Store<br/>Collection: autosar_hld_knowledge<br/>HNSW Cosine Vector Index")]
        SQLITE[("SQLite Audit Database<br/>rag_audit_log.db<br/>Table: audit_logs")]
        LOCAL_PDF[("Local PDF Storage<br/>Input_Data/HLD_BodyControl_v1.pdf<br/>Input_Data/HLD_BodyControl_v2.pdf")]
    end

    subgraph MODELS ["Local Embedded Inference Engines"]
        OLLAMA["Ollama Local Daemon<br/>(qwen2.5:3b / qwen2.5:7b @ :11434)"]
        EMBED["SentenceTransformer<br/>(BAAI/bge-small-en-v1.5 - 384 Dim)"]
    end

    %% UI to Orchestration
    UI_QA --> INJ_DEF
    INJ_DEF --> RET_ENG
    RET_ENG --> EMBED
    EMBED --> CHROMA
    CHROMA --> RET_ENG

    %% Refusal Gate & Execution
    RET_ENG --> REF_GATE
    REF_GATE -- "Context Supported" --> LLM_CALL
    REF_GATE -- "Insufficient Evidence" --> VAL_CHK
    LLM_CALL --> OLLAMA
    LLM_CALL -- "Daemon Offline" --> EXT_FALL
    OLLAMA --> VAL_CHK
    EXT_FALL --> VAL_CHK

    %% Post-Check & Logging
    VAL_CHK --> SQLITE
    VAL_CHK --> UI_QA
```

---

## 2. Ingestion & Section-Aware Chunking Pipeline

This pipeline transforms unstructured automotive PDF specifications into structured, searchable dense vector representations while preserving table layouts and hierarchical metadata:

```mermaid
graph LR
    subgraph INGEST ["1. Parsing & Extraction (Code/ingest.py)"]
        PDF_SRC["HLD Specification PDF<br/>(14 Pages)"]
        FITZ["PyMuPDF (fitz)<br/>Page-Indexed Text Extraction"]
        PLUMB["pdfplumber<br/>High-Fidelity Table Grid Parsing"]
        PDF_SRC --> FITZ
        PDF_SRC --> PLUMB
    end

    subgraph CHUNKING ["2. Chunking Engine (Code/chunk_embed.py)"]
        SEC_SPLIT["Section Boundary Detector<br/>(H1 & H2 Headers)"]
        TBL_PRE["Table Markdown Converter<br/>(Repeated Headers on Split)"]
        CHUNK_META["Metadata Enrichment<br/>doc_id, version, page, section, chunk_type"]
        FITZ --> SEC_SPLIT
        PLUMB --> TBL_PRE
        SEC_SPLIT --> CHUNK_META
        TBL_PRE --> CHUNK_META
    end

    subgraph EMBEDDING ["3. Embedding & Storage"]
        BGE["BAAI/bge-small-en-v1.5<br/>Dense Embedding Model"]
        VEC_DB[("ChromaDB Vector Store<br/>Code/chroma_db_store")]
        CHUNK_META --> BGE
        BGE --> VEC_DB
    end
```

---

## 3. Deterministic Architectural Revision Comparison Pipeline

To meet safety-critical ISO 26262 requirements, discrepancies between architectural revisions are detected strictly via deterministic rule evaluation, while the LLM is restricted solely to explaining engineering implications:

```mermaid
graph TD
    subgraph INPUTS ["Input Architecture Baselines"]
        V1_DATA["Extracted Entities v1.0<br/>(10 SWCs, 11 Interfaces, 12 Signals)"]
        V2_DATA["Extracted Entities v2.0<br/>(ECN Revision with 6 Seeded Changes)"]
    end

    subgraph DETECTOR ["Deterministic Rule Engine (Code/compare.py)"]
        R1["Rule 1: Renamed Signal Detector<br/>(Cycle time, bus, and endpoints invariant)"]
        R2["Rule 2: Removed Port Detector<br/>(PPort/RPort missing from SWC definition)"]
        R3["Rule 3: Data Type Mismatch Detector<br/>(e.g., Uint16 -> Float32 across RTE)"]
        R4["Rule 4: Undefined Component Reference<br/>(Component cited in flow/dependency but absent in inventory)"]
        R5["Rule 5: Orphaned Interface Detector<br/>(PPort provides interface with zero consumers)"]
    end

    subgraph REPORT ["Output Inconsistency Deliverables"]
        DIFF_JSON[("Evaluation_Results/inconsistency_report.json")]
        DIFF_MD["Evaluation_Results/inconsistency_report.md<br/>(Severity, ISO 26262 Impact & Action Items)"]
        LLM_EXP["Local LLM Functional Impact Explainer<br/>(Advisory commentary without hallucinating changes)"]
    end

    V1_DATA --> DETECTOR
    V2_DATA --> DETECTOR
    DETECTOR --> R1
    DETECTOR --> R2
    DETECTOR --> R3
    DETECTOR --> R4
    DETECTOR --> R5
    R1 --> DIFF_JSON
    R2 --> DIFF_JSON
    R3 --> DIFF_JSON
    R4 --> DIFF_JSON
    R5 --> DIFF_JSON
    DIFF_JSON --> LLM_EXP
    LLM_EXP --> DIFF_MD
```

---

## 4. Hardware Sizing & Offline Execution Profile

- **RAM Footprint:** ~2.1 GB RSS (ChromaDB + SentenceTransformer + Streamlit daemon). Fits comfortably within 12 GB RAM budget.
- **VRAM Utilization:** 0 GB required (CPU inference for embeddings; Ollama CPU/GPU offload for `qwen2.5:3b`).
- **External Outbound Ports:** None. All communication occurs over `localhost:8501` (Streamlit HTTP) and `localhost:11434` (Ollama REST).
