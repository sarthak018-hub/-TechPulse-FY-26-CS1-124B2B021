#!/usr/bin/env python3
"""
Section-Aware Chunking and BGE-Small Embedding Module
Chunks AUTOSAR HLD documents with section awareness and table integrity.
Embeds using BAAI/bge-small-en-v1.5 and stores in ChromaDB vector database.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from ingest import AUTOSARDocumentIngester

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AUTOSAR_ChunkEmbed")

DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db_store"
COLLECTION_NAME = "autosar_bcm_kb"


class SectionAwareChunker:
    """
    Chunks AUTOSAR HLD documents while preserving section boundaries,
    keeping tables intact as markdown representations, and capturing rich metadata.
    """
    def __init__(self, target_chunk_size: int = 500, chunk_overlap: int = 80):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """Converts extracted 2D table grid to a clean Markdown table."""
        if not table or len(table) < 2:
            return ""
        headers = table[0]
        md_lines = ["| " + " | ".join(headers) + " |"]
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in table[1:]:
            padded_row = row + [""] * (len(headers) - len(row))
            md_lines.append("| " + " | ".join(padded_row[:len(headers)]) + " |")
        return "\n".join(md_lines)

    def chunk_document(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        doc_id = parsed_doc["doc_id"]
        version = parsed_doc["version"]
        chunks = []
        global_chunk_idx = 0

        for page in parsed_doc["pages"]:
            page_num = page["page_number"]

            # 1. Chunk tables whole (or grouped rows)
            for t_idx, table in enumerate(page.get("tables", [])):
                md_table = self._table_to_markdown(table)
                if md_table:
                    chunk_id = f"{doc_id}_{version}_p{page_num}_tbl_{t_idx}"
                    section_title = f"Page {page_num} Table {t_idx + 1}"
                    # Find matching section title if available
                    for sec in page.get("sections", []):
                        if sec.get("section_title") and sec["section_title"] != "General":
                            section_title = sec["section_title"]
                            break

                    chunk_text = (
                        f"[Document: {doc_id} {version} | Page: {page_num} | Section: {section_title} | Type: Table]\n"
                        f"{md_table}"
                    )
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "doc_id": doc_id,
                            "version": version,
                            "page": int(page_num),
                            "section": str(section_title),
                            "chunk_type": "table",
                            "project_id": "PCCOE_AUTOSAR_ASSISTANT"
                        }
                    })
                    global_chunk_idx += 1

            # 2. Chunk text sections
            for sec_idx, sec in enumerate(page.get("sections", [])):
                sec_title = sec.get("section_title", f"Section Page {page_num}")
                content = sec.get("content", "").strip()
                if not content or len(content) < 30:
                    continue

                is_flow = "Flow " in sec_title or "Sequence" in sec_title or "Execution Steps" in content
                chunk_type = "flow" if is_flow else "text"

                # If text is small, keep as single chunk
                if len(content) <= self.target_chunk_size + 100:
                    chunk_id = f"{doc_id}_{version}_p{page_num}_sec{sec_idx}_c0"
                    header_line = f"[Document: {doc_id} {version} | Page: {page_num} | Section: {sec_title} | Type: {chunk_type.capitalize()}]\n"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": header_line + content,
                        "metadata": {
                            "doc_id": doc_id,
                            "version": version,
                            "page": int(page_num),
                            "section": str(sec_title),
                            "chunk_type": chunk_type,
                            "project_id": "PCCOE_AUTOSAR_ASSISTANT"
                        }
                    })
                    global_chunk_idx += 1
                else:
                    # Sliding window with overlap
                    start = 0
                    sub_idx = 0
                    while start < len(content):
                        end = min(start + self.target_chunk_size, len(content))
                        # Prefer breaking on newline or sentence
                        if end < len(content):
                            newline_pos = content.rfind("\n", start + 200, end)
                            if newline_pos != -1:
                                end = newline_pos + 1
                            else:
                                period_pos = content.rfind(". ", start + 200, end)
                                if period_pos != -1:
                                    end = period_pos + 2

                        slice_text = content[start:end].strip()
                        if slice_text:
                            chunk_id = f"{doc_id}_{version}_p{page_num}_sec{sec_idx}_c{sub_idx}"
                            header_line = f"[Document: {doc_id} {version} | Page: {page_num} | Section: {sec_title} | Type: {chunk_type.capitalize()}]\n"
                            chunks.append({
                                "chunk_id": chunk_id,
                                "text": header_line + slice_text,
                                "metadata": {
                                    "doc_id": doc_id,
                                    "version": version,
                                    "page": int(page_num),
                                    "section": str(sec_title),
                                    "chunk_type": chunk_type,
                                    "project_id": "PCCOE_AUTOSAR_ASSISTANT"
                                }
                            })
                            global_chunk_idx += 1
                            sub_idx += 1

                        if end >= len(content):
                            break
                        start = max(start + 1, end - self.chunk_overlap)

        logger.info(f"Chunked {doc_id}_{version} into {len(chunks)} section-aware chunks.")
        return chunks


class AUTOSARVectorStore:
    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL, persist_dir: Path = CHROMA_DIR):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name

        logger.info(f"Loading embedding model: {self.model_name}...")
        self.embed_model = SentenceTransformer(self.model_name)

        logger.info(f"Initializing persistent ChromaDB client at: {self.persist_dir}...")
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "AUTOSAR BCM Knowledge Base"}
        )

    def index_document(self, parsed_doc: Dict[str, Any], chunker: Optional[SectionAwareChunker] = None) -> int:
        if chunker is None:
            chunker = SectionAwareChunker()

        chunks = chunker.chunk_document(parsed_doc)
        if not chunks:
            logger.warning(f"No chunks generated for {parsed_doc.get('doc_id')}")
            return 0

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embed_model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        embeddings_list = embeddings.tolist()

        logger.info(f"Upserting {len(ids)} chunks into ChromaDB collection '{COLLECTION_NAME}'...")
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings_list,
            metadatas=metadatas
        )
        logger.info(f"[SUCCESS] Successfully indexed {len(ids)} chunks into ChromaDB.")
        return len(ids)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        version_filter: Optional[str] = None,
        type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves top-k chunks with optional version or type filtering."""
        query_emb = self.embed_model.encode([query], normalize_embeddings=True).tolist()

        where_clause = None
        conditions = []
        if version_filter:
            conditions.append({"version": version_filter.lower()})
        if type_filter:
            conditions.append({"chunk_type": type_filter})

        if len(conditions) == 1:
            where_clause = conditions[0]
        elif len(conditions) > 1:
            where_clause = {"$and": conditions}

        retrieved_chunks = []
        try:
            results = self.collection.query(
                query_embeddings=query_emb,
                n_results=k,
                where=where_clause
            )
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chunk_id = results["ids"][0][i]
                    doc_text = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
                    similarity = round(1.0 - (distance / 2.0), 4)

                    retrieved_chunks.append({
                        "chunk_id": chunk_id,
                        "text": doc_text,
                        "metadata": metadata,
                        "distance": distance,
                        "similarity": similarity
                    })
        except Exception as e:
            logger.warning(f"ChromaDB HNSW query error ({e}), applying exact embedding similarity fallback...")
            # Fallback to exact cosine search across filtered embeddings
            records = self.collection.get(
                where=where_clause,
                include=["documents", "metadatas", "embeddings"]
            )
            if records and records["ids"]:
                import numpy as np
                q_vec = np.array(query_emb[0])
                all_embs = np.array(records["embeddings"])
                sims = np.dot(all_embs, q_vec)
                top_indices = np.argsort(sims)[::-1][:k]

                for idx in top_indices:
                    sim_val = round(float(sims[idx]), 4)
                    retrieved_chunks.append({
                        "chunk_id": records["ids"][idx],
                        "text": records["documents"][idx],
                        "metadata": records["metadatas"][idx],
                        "distance": round(float(1.0 - sim_val), 4),
                        "similarity": sim_val
                    })

        return retrieved_chunks


def main():
    base_dir = Path(__file__).resolve().parent.parent
    input_dir = base_dir / "Input_Data"

    ingester = AUTOSARDocumentIngester()
    chunker = SectionAwareChunker(target_chunk_size=500, chunk_overlap=80)
    store = AUTOSARVectorStore()

    # Index v1 baseline
    v1_pdf = input_dir / "HLD_BodyControl_v1.pdf"
    if v1_pdf.exists():
        logger.info("Ingesting and indexing HLD_BodyControl_v1.pdf...")
        doc1 = ingester.ingest_pdf(str(v1_pdf), version="v1")
        count1 = store.index_document(doc1, chunker)
        print(f"Indexed v1: {count1} chunks")

    # Index v2 revision
    v2_pdf = input_dir / "HLD_BodyControl_v2.pdf"
    if v2_pdf.exists():
        logger.info("Ingesting and indexing HLD_BodyControl_v2.pdf...")
        doc2 = ingester.ingest_pdf(str(v2_pdf), version="v2")
        count2 = store.index_document(doc2, chunker)
        print(f"Indexed v2: {count2} chunks")

    # Retrieval Smoke Test
    test_query = "What happens to door locks when a crash pulse is detected?"
    print(f"\n[QUERY TEST] Query: '{test_query}'")
    results = store.similarity_search(test_query, k=3, version_filter="v1")
    for idx, r in enumerate(results, 1):
        meta = r["metadata"]
        print(f"  Result {idx} [Similarity: {r['similarity']}]: {r['chunk_id']} (Page {meta['page']}, {meta['section']})")
        first_line = r['text'].split('\n')[1] if '\n' in r['text'] else r['text'][:80]
        print(f"    Snippet: {first_line[:90]}...")


if __name__ == "__main__":
    main()
