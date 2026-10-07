#!/usr/bin/env python3
"""
AUTOSAR HLD Document Analysis Assistant - Streamlit Web Application
Features:
1. Advisory Banner: 'AI-assisted output. Requires engineer review.'
2. Tabs:
   - Upload & Ingest: Upload PDF with version label and index into ChromaDB
   - Q&A Assistant: Grounded query with citations, confidence badge, and expandable source chunks
   - Entity Explorer: Interactive inspection of components, interfaces, signals, and ports
   - Revision Compare: Compare v1 vs v2 with inconsistency report and severity breakdown
   - Export Center: Download CSV and JSON entity catalogs & markdown reports
   - Compliance Audit Log: Real-time inspection of SQLite audit trail
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path

# Add Code directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
CODE_DIR = BASE_DIR / "Code"
INPUT_DATA_DIR = BASE_DIR / "Input_Data"
EVAL_RESULTS_DIR = BASE_DIR / "Evaluation_Results"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from ingest import AUTOSARDocumentIngester
from chunk_embed import AUTOSARVectorStore, SectionAwareChunker
from rag import AUTOSARRAGPipeline, AUDIT_DB_PATH
from extract_entities import AUTOSAREntityExtractor
from compare import AUTOSARRevisionComparator

st.set_page_config(
    page_title="AUTOSAR HLD Analysis Assistant",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished automotive engineering aesthetic
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 15px;
    }
    .advisory-banner {
        background-color: #fef2f2;
        border-left: 5px solid #ef4444;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 600;
        color: #991b1b;
        margin-bottom: 18px;
    }
    .badge-high {
        background-color: #dcfce7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-low {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 12px;
    }
    .citation-tag {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        font-family: monospace;
        margin-right: 4px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rag_pipeline():
    return AUTOSARRAGPipeline()


@st.cache_resource
def get_entity_extractor():
    return AUTOSAREntityExtractor()


@st.cache_resource
def get_revision_comparator():
    return AUTOSARRevisionComparator()


# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/car-service.png", width=64)
st.sidebar.title("AUTOSAR Assistant")
st.sidebar.caption("PCCOE AI/ML Final Year Project")
st.sidebar.markdown("---")

current_user = st.sidebar.text_input("Active User / Engineer", value="Sarthak (Engineer)")
selected_version = st.sidebar.selectbox("Active Baseline / Document Version", options=["v1", "v2"], index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### System Health")
st.sidebar.success("Local Embeddings: BGE-small-v1.5")
st.sidebar.info("Vector Store: ChromaDB (Persistent)")
st.sidebar.info("LLM Backend: Local Ollama / Deterministic Grounding")

# Header & Advisory Banner
st.markdown('<div class="main-header">AUTOSAR HLD Document Analysis Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">RAG-Based Automotive Architecture Review, Entity Traceability & Inconsistency Verification</div>', unsafe_allow_html=True)
st.markdown('<div class="advisory-banner">⚠️ AI-assisted output. Requires engineer review. All extracted data and citations are advisory.</div>', unsafe_allow_html=True)

# Main Navigation Tabs
tabs = st.tabs([
    "💬 Q&A Assistant",
    "📤 Upload & Ingest",
    "🔍 Entity Explorer",
    "⚖️ Revision Compare",
    "📦 Export Center",
    "📋 Compliance Audit Log"
])

# ================= TAB 1: Q&A ASSISTANT =================
with tabs[0]:
    st.markdown("### Architectural Knowledge Retrieval")
    st.write("Ask natural-language questions about software components, port interfaces, signals, functional flows, and diagnostics.")

    preset_queries = [
        "Custom query...",
        "What happens to door locks when a crash pulse is detected?",
        "What is the auto-lock speed threshold?",
        "What is the data type of VehicleSpeedKmh in v2?",
        "Which component provides If_LightingCommand?",
        "What is the turbocharger boost pressure?"
    ]
    chosen_preset = st.selectbox("Quick Query Templates:", preset_queries, index=1)

    if chosen_preset == "Custom query...":
        user_query = st.text_input("Enter Question:", placeholder="e.g. Which components interface with p_CrashStatus?")
    else:
        user_query = st.text_input("Enter Question:", value=chosen_preset)

    col_btn, col_k = st.columns([1, 4])
    with col_btn:
        ask_btn = st.button("Submit Query", type="primary", use_container_width=True)

    if ask_btn and user_query:
        rag = get_rag_pipeline()
        with st.spinner("Retrieving grounded evidence from ChromaDB..."):
            res = rag.query(user_query, version_filter=selected_version, user=current_user)

        st.markdown("---")
        st.markdown("#### Answer")
        st.write(res["answer"])

        # Badges and citations
        conf = res["confidence"]
        badge_class = f"badge-{conf.lower()}"
        col_c1, col_c2 = st.columns([1, 3])
        with col_c1:
            st.markdown(f"**Confidence:** <span class='{badge_class}'>{conf}</span>", unsafe_allow_html=True)
        with col_c2:
            if res["citations"]:
                st.markdown("**Citations:** " + " ".join([f"<span class='citation-tag'>{c}</span>" for c in res["citations"]]), unsafe_allow_html=True)
            else:
                st.markdown("**Citations:** *None (Refusal / Insufficient evidence)*")

        st.caption(f"ℹ️ {res['limitation_note']}")

        # Expandable retrieved chunks
        with st.expander(f"📑 View Retrieved Context Chunks ({len(res['retrieved_chunks'])} retrieved)"):
            for idx, c in enumerate(res["retrieved_chunks"], 1):
                meta = c["metadata"]
                st.markdown(f"**Chunk {idx}:** `{c['chunk_id']}` | **Page:** {meta.get('page')} | **Section:** {meta.get('section')} | **Cosine Similarity:** `{c['similarity']}`")
                st.text(c["text"])
                st.markdown("---")

# ================= TAB 2: UPLOAD & INGEST =================
with tabs[1]:
    st.markdown("### Document Upload & Ingestion Engine")
    st.write("Upload a High-Level Design PDF specification to parse structure, extract tables, and index chunks into ChromaDB.")

    col_u1, col_u2 = st.columns([2, 1])
    with col_u1:
        uploaded_file = st.file_uploader("Select AUTOSAR HLD PDF", type=["pdf"])
    with col_u2:
        doc_version_input = st.selectbox("Assign Document Version Label", options=["v1", "v2", "v3-custom"])

    if uploaded_file is not None:
        save_path = INPUT_DATA_DIR / uploaded_file.name
        if st.button("Process & Index Document", type="primary"):
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File uploaded to {save_path.name}")

            with st.spinner("Ingesting PDF text, headings, and tables..."):
                ingester = AUTOSARDocumentIngester()
                parsed = ingester.ingest_pdf(str(save_path), version=doc_version_input)

            with st.spinner("Embedding section-aware chunks into ChromaDB..."):
                store = AUTOSARVectorStore()
                chunk_count = store.index_document(parsed)

            st.success(f"Successfully indexed {chunk_count} section-aware chunks into ChromaDB!")

    st.markdown("---")
    st.markdown("#### Existing Ingested Documents in Knowledge Base")
    existing_pdfs = list(INPUT_DATA_DIR.glob("*.pdf"))
    if existing_pdfs:
        for p in existing_pdfs:
            st.markdown(f"• **{p.name}** ({p.stat().st_size / 1024:.1f} KB)")
    else:
        st.info("No documents currently stored.")

# ================= TAB 3: ENTITY EXPLORER =================
with tabs[2]:
    st.markdown("### Architectural Entity Explorer")
    st.write("Browse structured inventories of software components, port interfaces, signals, and dependencies extracted from the HLD.")

    entity_type = st.radio("Select Entity Catalog:", ["Components", "Interfaces", "Signals", "Dependencies"], horizontal=True)

    json_file = INPUT_DATA_DIR / f"extracted_entities_HLD_BodyControl_{selected_version}.json"
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if entity_type == "Components":
            df = pd.DataFrame(data.get("components", []))
            st.dataframe(df, use_container_width=True)
        elif entity_type == "Interfaces":
            df = pd.DataFrame(data.get("interfaces", []))
            st.dataframe(df, use_container_width=True)
        elif entity_type == "Signals":
            df = pd.DataFrame(data.get("signals", []))
            st.dataframe(df, use_container_width=True)
        elif entity_type == "Dependencies":
            df = pd.DataFrame(data.get("dependencies", []))
            st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"Extracted entity catalog for {selected_version} not found. Run Step 5 extraction first.")

# ================= TAB 4: REVISION COMPARE =================
with tabs[3]:
    st.markdown("### Revision Comparison & Inconsistency Detection")
    st.write("Deterministic comparison between Baseline (v1) and Revised (v2) specifications.")

    v1_file = INPUT_DATA_DIR / "HLD_BodyControl_v1.pdf"
    v2_file = INPUT_DATA_DIR / "HLD_BodyControl_v2.pdf"

    if st.button("Run Deterministic Revision Comparison (v1 vs v2)", type="primary"):
        if v1_file.exists() and v2_file.exists():
            comparator = get_revision_comparator()
            with st.spinner("Analyzing structural differences and architectural coupling..."):
                rep = comparator.compare_revisions(str(v1_file), str(v2_file))
                rep_md_path = EVAL_RESULTS_DIR / "inconsistency_report.md"
                comparator.generate_markdown_report(rep, rep_md_path)
            st.success(f"Detected {rep['total_defects_detected']} architectural inconsistencies!")
        else:
            st.error("Missing baseline or revision PDF files in Input_Data/")

    report_json_path = EVAL_RESULTS_DIR / "inconsistency_report.json"
    if report_json_path.exists():
        with open(report_json_path, "r", encoding="utf-8") as f:
            rep = json.load(f)

        st.markdown("#### Summary of Detected Findings")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Inconsistencies", rep["total_defects_detected"])
        col_m2.metric("Critical / High Severity", len([i for i in rep["inconsistencies"] if i["severity"] in ["Critical", "High"]]))
        col_m3.metric("Medium / Low Severity", len([i for i in rep["inconsistencies"] if i["severity"] in ["Medium", "Low"]]))

        # Category Breakdown
        st.write("**Defects by Category:**")
        st.json(rep["summary_by_category"])

        st.markdown("#### Detailed Inconsistency Records")
        df_inc = pd.DataFrame(rep["inconsistencies"])
        st.dataframe(df_inc[["id", "category", "severity", "entity", "citation", "explanation"]], use_container_width=True)
    else:
        st.info("Run the comparison to generate the inconsistency report.")

# ================= TAB 5: EXPORT CENTER =================
with tabs[4]:
    st.markdown("### Export & Artifact Center")
    st.write("Download structured CSV/JSON entity inventories, defect catalogs, and compliance reports.")

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown("#### CSV Data Exports")
        for csv_path in INPUT_DATA_DIR.glob("*.csv"):
            with open(csv_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ Download {csv_path.name}",
                    data=f.read(),
                    file_name=csv_path.name,
                    mime="text/csv",
                    use_container_width=True
                )

    with col_e2:
        st.markdown("#### Formal Reports & Ground Truth")
        report_md_file = EVAL_RESULTS_DIR / "inconsistency_report.md"
        if report_md_file.exists():
            with open(report_md_file, "r", encoding="utf-8") as f:
                st.download_button(
                    label="⬇️ Download Inconsistency Report (Markdown)",
                    data=f.read(),
                    file_name="inconsistency_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )

        gt_file = INPUT_DATA_DIR / "seeded_defects_ground_truth.json"
        if gt_file.exists():
            with open(gt_file, "r", encoding="utf-8") as f:
                st.download_button(
                    label="⬇️ Download Seeded Defects Ground Truth (JSON)",
                    data=f.read(),
                    file_name="seeded_defects_ground_truth.json",
                    mime="application/json",
                    use_container_width=True
                )

# ================= TAB 6: COMPLIANCE AUDIT LOG =================
with tabs[5]:
    st.markdown("### SQLite Compliance Audit Log")
    st.write("Immutable query and retrieval audit records logged in SQLite (`rag_audit_log.db`).")

    if AUDIT_DB_PATH.exists():
        conn = sqlite3.connect(AUDIT_DB_PATH)
        df_audit = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50", conn)
        conn.close()

        if not df_audit.empty:
            st.dataframe(df_audit, use_container_width=True)
            st.caption(f"Displaying latest {len(df_audit)} queries recorded.")
        else:
            st.info("No queries recorded yet in the audit log.")
    else:
        st.info("Audit database has not yet been initialized.")
