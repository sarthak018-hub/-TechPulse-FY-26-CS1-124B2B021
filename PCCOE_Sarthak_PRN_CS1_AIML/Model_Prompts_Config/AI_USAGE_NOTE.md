# Declaration of AI Assistance in Project Development (AI Usage Note)

> **Student Name:** Sarthak  
> **Course / Degree:** B.E. / B.Tech Computer Engineering (AI & ML Specialization)  
> **Institution:** Pimpri Chinchwad College of Engineering (PCCOE), Pune  
> **Project Title:** AUTOSAR HLD Document Analysis Assistant  
> **Academic Year:** 2026  

---

## 1. Academic Integrity & Transparency Statement

In compliance with PCCOE academic integrity guidelines, ethical AI development standards, and university project submission requirements, this document transparently delineates the exact scope, boundaries, and nature of AI assistance utilized during the conception, development, and evaluation of this engineering project.

---

## 2. AI Tools Utilized

- **Primary Coding Assistant:** Antigravity AI Pair-Programming Assistant (Google DeepMind Agentic Coding Environment).
- **Underlying Local Inference Models:** `qwen2.5:3b` and `BAAI/bge-small-en-v1.5` (offline local components of the project artifact itself).

---

## 3. Scope of AI-Assisted Implementation

AI assistance was selectively utilized as an accelerated pair-programming and refactoring partner for repetitive software engineering workflows:

1. **Folder Scaffolding & Packaging:** Generating automated directory structure creation logic and `make_submission_zip.py` verification scripts.
2. **Synthetic Data Boilerplate:** Generating procedural ReportLab flowable layout code (`Code/generate_synthetic_data.py`) to render multi-page tables, headers, and footers.
3. **Regex & String Heuristics:** Accelerating regular expression pattern generation for extracting signal tables, port declarations, and ISO 14229 DTC rows.
4. **Streamlit Component Layout:** Assisting with UI component layouts (tab structures, card metrics, download buttons, and badge styling).
5. **Code Documentation & Typing:** Formatting standard Python type hints, docstrings, and clean exception handling blocks.

---

## 4. Student Independent Design, Authoring, and Validation

The intellectual, architectural, and analytical core of the project was conceptualized, designed, and verified independently by the student:

1. **AUTOSAR Domain Architecture Modeling:**
   - Conceptualization of the Body Control Module (BCM) software component architecture according to Classic AUTOSAR Release 4.4.0.
   - Definition of 10 distinct Application and Bridge SWCs, ASIL risk allocations (ISO 26262:2018), and physical transceiver pinouts.
2. **Architectural Defect Injection Design:**
   - Formulation of the 5 defect categories: renamed signals, removed ports, changed data types, undefined referenced components, and orphaned interfaces.
   - Engineering the exact behavioral delta between `HLD_BodyControl_v1.pdf` and `HLD_BodyControl_v2.pdf`.
3. **Defensive RAG Refusal Architecture:**
   - Conception and tuning of the dual-stage refusal gate (cosine similarity threshold + substantive keyword ratio check) to eliminate automotive hallucination.
   - Design of strict citation post-checking (`[doc_id, version, page N, section]`).
4. **Ground-Truth Evaluation Benchmark:**
   - Authoring the 20-question evaluation test suite in `Evaluation_Results/questions_ground_truth.csv`.
   - Hand-verifying every factual answer, gold page, and gold section directly against the PDF source.
5. **Local Offline-Only Constraints & Debugging:**
   - Diagnosing ChromaDB small-collection HNSW dimensional filter edge cases and developing the robust cosine dot-product fallback.
   - Enforcing strict zero-cloud runtime isolation for IP security.

---

## 5. Summary Conclusion

The AI coding assistant functioned strictly as an accelerator for syntax generation and boilerplate automation. All system architecture decisions, domain models, verification suites, and defect classification logic represent the independent engineering work and intellectual property of the student.

---

*Signed by Student and submitted for academic evaluation.*
