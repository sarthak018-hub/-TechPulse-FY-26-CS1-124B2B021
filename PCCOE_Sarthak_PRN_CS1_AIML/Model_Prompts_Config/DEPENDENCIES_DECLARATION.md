# Dependencies & Offline Runtime Declaration

> **Project:** AUTOSAR HLD Document Analysis Assistant  
> **Institution:** Pimpri Chinchwad College of Engineering (PCCOE), Pune  
> **Department:** Computer Engineering / AI & ML Lab  
> **Classification:** Academic Engineering Submission (Offline RAG System)  

---

## 1. Zero External Runtime API Declaration

We hereby declare that the **AUTOSAR HLD Document Analysis Assistant** operates **100% offline** during live execution.

- **Zero Third-Party Cloud APIs:** The pipeline does **NOT** invoke OpenAI (GPT-4/ChatGPT), Anthropic (Claude), Google Gemini, AWS Bedrock, or any external SaaS LLM API.
- **Zero Outbound Telemetry:** No user queries, retrieved architectural chunks, citations, or entity data are transmitted across the network.
- **Strict Data Privacy:** Intellectual property in automotive High-Level Design (HLD) specifications remains strictly confined to the local host machine at all times.

---

## 2. One-Time Setup Downloads (Pre-requisites)

To enable fully offline local inference, the following one-time downloads are performed during initial environment setup:

### A. Python Virtual Environment Dependencies
- **Command:** `pip install -r Code/requirements.txt`
- **Origin:** Standard Python Package Index (PyPI).
- **Scope:** Pinned Python packages for PDF extraction, vector indexing, UI rendering, and testing.

### B. Dense Embedding Weights
- **Model Tag:** `BAAI/bge-small-en-v1.5`
- **Source:** Hugging Face Model Hub (`https://huggingface.co/BAAI/bge-small-en-v1.5`)
- **Download Size:** ~133 MB (ONNX / SafeTensors format)
- **Local Cache Path:** `%USERPROFILE%\.cache\huggingface\hub\models--BAAI--bge-small-en-v1.5`
- **Runtime Mode:** Loaded directly from the local disk cache by `sentence_transformers.SentenceTransformer`.

### C. Local Quantized Large Language Model
- **Primary Model Tag:** `qwen2.5:3b` (Q4_K_M quantization, ~1.9 GB)
- **Alternative Model Tag:** `qwen2.5:7b` (Q4_K_M quantization, ~4.7 GB, for workstations with ≥16 GB RAM)
- **Engine:** Ollama Local Daemon (`http://localhost:11434`)
- **Command:** `ollama pull qwen2.5:3b`
- **Local Storage Path:** `%USERPROFILE%\.ollama\models`

---

## 3. Offline Verification Procedure for Examiners

Evaluators and examiners can independently verify the offline integrity of this system through the following test protocol:

1. **Disconnect Network Adapter:**
   - Disconnect Wi-Fi and unplug all Ethernet cables from the evaluation workstation.
2. **Launch Streamlit Web Interface:**
   ```bash
   cd PCCOE_Sarthak_PRN_CS1_AIML
   .venv\Scripts\streamlit run Code\app.py
   ```
3. **Execute Benchmark Evaluation:**
   ```bash
   .venv\Scripts\python Code\evaluate.py
   ```
4. **Inspect Audit Log:**
   - Open `Code/rag_audit_log.db` using any SQLite viewer. Verify all 20 benchmark queries executed locally with 0 network packet transmission.
5. **Deterministic Extractive Fallback Verification:**
   - Terminate the Ollama daemon (`taskkill /f /im ollama.exe`).
   - Query the assistant in the Web UI: the built-in deterministic extractor seamlessly handles the query locally using semantic sentence matching and strict citation enforcement without raising network connection errors.

---

*Signed and certified for academic compliance.*
