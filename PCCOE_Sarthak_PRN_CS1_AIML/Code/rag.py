#!/usr/bin/env python3
"""
RAG Pipeline Module for AUTOSAR HLD Document Assistant
Features:
- Top-k retrieval with metadata filtering (version, chunk type)
- Prompt injection defense: separates untrusted context from instructions
- Strict citation formatting [doc_id, version, page N, section]
- Post-check groundedness and citation verification
- SQLite audit logging
- Local Ollama LLM interface with deterministic fallback
"""

import os
import sys
import json
import re
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import ollama
from chunk_embed import AUTOSARVectorStore, DEFAULT_EMBED_MODEL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AUTOSAR_RAG")

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "Model_Prompts_Config" / "prompts"
AUDIT_DB_PATH = Path(__file__).resolve().parent / "rag_audit_log.db"
DEFAULT_LLM_MODEL = "qwen2.5:3b"


class RAGPostCheckError(Exception):
    """Raised when answer violates citation or groundedness rules."""
    pass


class AUTOSARRAGPipeline:
    def __init__(
        self,
        llm_model: str = DEFAULT_LLM_MODEL,
        temperature: float = 0.1,
        top_k: int = 4,
        similarity_threshold: float = 0.68
    ):
        self.llm_model = llm_model
        self.temperature = temperature
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        self.vector_store = AUTOSARVectorStore()
        self.system_prompt = self._load_prompt("rag_system_prompt.txt")
        self.user_template = self._load_prompt("rag_user_template.txt")
        self._init_audit_db()

    def _load_prompt(self, filename: str) -> str:
        prompt_path = PROMPTS_DIR / filename
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        logger.warning(f"Prompt file {filename} not found at {prompt_path}. Using internal default.")
        return ""

    def _init_audit_db(self) -> None:
        """Initializes SQLite audit database for query tracking and compliance."""
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                query TEXT NOT NULL,
                version_filter TEXT,
                retrieved_chunk_ids TEXT NOT NULL,
                answer TEXT NOT NULL,
                citations TEXT NOT NULL,
                confidence TEXT NOT NULL,
                post_check_passed INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _log_audit_entry(
        self,
        query: str,
        version_filter: Optional[str],
        chunks: List[Dict[str, Any]],
        answer: str,
        citations: List[str],
        confidence: str,
        passed: bool,
        user: str = "Engineer"
    ) -> None:
        try:
            conn = sqlite3.connect(AUDIT_DB_PATH)
            cursor = conn.cursor()
            chunk_ids_str = json.dumps([c["chunk_id"] for c in chunks])
            citations_str = json.dumps(citations)
            cursor.execute("""
                INSERT INTO audit_logs 
                (timestamp, user, query, version_filter, retrieved_chunk_ids, answer, citations, confidence, post_check_passed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                user,
                query,
                version_filter or "all",
                chunk_ids_str,
                answer,
                citations_str,
                confidence,
                1 if passed else 0
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

    def retrieve_context(
        self,
        query: str,
        version_filter: Optional[str] = None,
        type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves top-k chunks with optional version and chunk_type filters."""
        return self.vector_store.similarity_search(
            query=query,
            k=self.top_k,
            version_filter=version_filter,
            type_filter=type_filter
        )

    def _generate_with_ollama(self, prompt: str) -> Optional[str]:
        """Invokes local Ollama server if available."""
        try:
            client = ollama.Client(host="http://localhost:11434")
            response = client.generate(
                model=self.llm_model,
                prompt=prompt,
                system=self.system_prompt,
                options={
                    "temperature": self.temperature,
                    "seed": 42
                }
            )
            return response.get("response", "").strip()
        except Exception as e:
            logger.debug(f"Ollama local LLM invocation unavailable ({e}). Using deterministic extractor.")
            return None

    def _deterministic_extractive_answer(self, query: str, chunks: List[Dict[str, Any]]) -> Tuple[str, List[str], str]:
        """
        Deterministic, offline extraction fallback that answers directly from retrieved chunks.
        Evaluates semantic sentence overlap across all top-k chunks and collects matching citations.
        Guarantees 100% test reproducibility even when Ollama server is offline.
        """
        if not chunks or chunks[0]["similarity"] < self.similarity_threshold:
            return "Not found in the provided document.", [], "Low"

        query_words = set(re.findall(r"\w+", query.lower())) - {
            "what", "is", "the", "how", "does", "in", "to", "and", "of", "for", "a", "an",
            "when", "are", "which", "with", "where", "why", "under", "between", "regarding"
        }

        # Evaluate candidate sentences across all retrieved chunks
        candidates = []
        for chunk in chunks:
            meta = chunk["metadata"]
            citation = f"[{meta['doc_id']}, {meta['version']}, page {meta['page']}, {meta['section']}]"
            text_content = chunk["text"]
            if "\n" in text_content:
                clean_text = text_content.split("\n", 1)[1].strip()
            else:
                clean_text = text_content

            # Split on sentence boundaries and table row breaks
            segments = re.split(r"(?<=[.!?])\s+|\n+", clean_text)
            for seg in segments:
                seg = seg.strip()
                if not seg or len(seg) < 15:
                    continue
                seg_words = set(re.findall(r"\w+", seg.lower()))
                overlap = query_words.intersection(seg_words)
                if overlap:
                    candidates.append((len(overlap), seg, citation, chunk["similarity"]))

        if candidates:
            # Sort by keyword overlap descending, then by chunk similarity
            candidates.sort(key=lambda x: (x[0], x[3]), reverse=True)
            top_cands = candidates[:3]
            answer_text = " ".join([c[1] for c in top_cands]).strip()
            citations = []
            for c in top_cands:
                if c[2] not in citations:
                    citations.append(c[2])
        else:
            top_chunk = chunks[0]
            meta = top_chunk["metadata"]
            citations = [f"[{meta['doc_id']}, {meta['version']}, page {meta['page']}, {meta['section']}]"]
            answer_text = top_chunk["text"][:350].strip()

        confidence = "High" if chunks[0]["similarity"] >= 0.70 else "Medium"
        return answer_text, citations, confidence

    def post_check_verification(
        self,
        answer: str,
        citations: List[str],
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, str, List[str]]:
        """
        Validates:
        1. Every cited chunk actually exists in retrieved context.
        2. Answer key terms appear in the retrieved context.
        Downgrades confidence or triggers refusal if ungrounded.
        """
        if "not found in the provided document" in answer.lower():
            return True, "High", []

        if not citations:
            return False, "Low", []

        # Validate that cited page/section matches at least one retrieved chunk
        retrieved_coords = []
        full_context_text = ""
        for c in retrieved_chunks:
            m = c["metadata"]
            retrieved_coords.append((m["version"].lower(), m["page"]))
            full_context_text += " " + c["text"].lower()

        valid_citations = []
        for cite in citations:
            # Match pattern: [doc, version, page N, section]
            page_match = re.search(r"page\s+(\d+)", cite, re.IGNORECASE)
            ver_match = re.search(r"\b(v1|v2)\b", cite, re.IGNORECASE)

            if page_match and ver_match:
                page_num = int(page_match.group(1))
                ver = ver_match.group(1).lower()
                if (ver, page_num) in retrieved_coords:
                    valid_citations.append(cite)

        if not valid_citations:
            logger.warning("Post-check failed: Citations did not match retrieved chunk pages.")
            return False, "Low", []

        # Groundedness term check: extract key alphanumeric identifiers (e.g. SWC names, DTCs, signals)
        key_tokens = re.findall(r"\b[A-Z][A-Za-z0-9_]{3,}\b|\b\d+\s*km/h\b|\b\d+\s*ms\b", answer)
        if key_tokens:
            unsupported = [t for t in key_tokens if t.lower() not in full_context_text]
            if len(unsupported) > len(key_tokens) * 0.5:
                logger.warning(f"Post-check warning: Key terms {unsupported} not found in retrieved chunks.")
                return False, "Low", valid_citations

        return True, "High", valid_citations

    def query(
        self,
        user_question: str,
        version_filter: Optional[str] = "v1",
        type_filter: Optional[str] = None,
        user: str = "Engineer"
    ) -> Dict[str, Any]:
        """
        Executes end-to-end RAG query:
        1. Retrieves relevant chunks with metadata filters.
        2. Formulates prompt with untrusted data isolation.
        3. Generates grounded answer via Ollama (or fallback).
        4. Validates citations and groundedness.
        5. Logs query in SQLite audit table.
        """
        logger.info(f"Processing RAG query: '{user_question}' (version={version_filter})")
        retrieved = self.retrieve_context(user_question, version_filter=version_filter, type_filter=type_filter)

        # Refusal Check 1: Similarity threshold gate
        if not retrieved or retrieved[0]["similarity"] < self.similarity_threshold:
            answer = "Not found in the provided document."
            citations = []
            confidence = "High"
            passed = True
            self._log_audit_entry(user_question, version_filter, retrieved, answer, citations, confidence, passed, user)
            return {
                "query": user_question,
                "answer": answer,
                "citations": citations,
                "confidence": confidence,
                "limitation_note": "Advisory output. Requires engineer review.",
                "post_check_passed": passed,
                "retrieved_chunks": retrieved
            }

        # Refusal Check 2: Substantive content keyword overlap check
        stopwords = {
            "what", "is", "the", "how", "does", "in", "to", "and", "of", "for", "a", "an",
            "when", "are", "which", "with", "where", "why", "from", "between", "under", "regarding"
        }
        q_keywords = [w.lower() for w in re.findall(r"\b[A-Za-z0-9_]{3,}\b", user_question) if w.lower() not in stopwords]
        combined_text = " ".join([c["text"].lower() for c in retrieved])
        overlap_kws = [kw for kw in q_keywords if kw in combined_text]
        overlap_ratio = len(overlap_kws) / len(q_keywords) if q_keywords else 0.0

        # If substantive question keywords have less than 35% overlap with retrieved context,
        # or no keywords match, the document lacks the necessary domain evidence.
        if not q_keywords or overlap_ratio < 0.35:
            answer = "Not found in the provided document."
            citations = []
            confidence = "High"
            passed = True
            self._log_audit_entry(user_question, version_filter, retrieved, answer, citations, confidence, passed, user)
            return {
                "query": user_question,
                "answer": answer,
                "citations": citations,
                "confidence": confidence,
                "limitation_note": "Advisory output. Requires engineer review.",
                "post_check_passed": passed,
                "retrieved_chunks": retrieved
            }

        # Build context block
        context_parts = []
        for idx, c in enumerate(retrieved, 1):
            m = c["metadata"]
            citation_str = f"[{m['doc_id']}, {m['version']}, page {m['page']}, {m['section']}]"
            context_parts.append(f"Chunk {idx} Citation: {citation_str}\n{c['text']}\n")
        context_block = "\n".join(context_parts)

        user_prompt = self.user_template.format(
            context_block=context_block,
            user_question=user_question
        )

        # Attempt Ollama generation
        raw_response = self._generate_with_ollama(user_prompt)

        if raw_response and "Answer:" in raw_response:
            # Parse structured response
            ans_match = re.search(r"Answer:\s*(.*?)(?=\nCitations:|\nConfidence:|$)", raw_response, re.DOTALL)
            cite_match = re.search(r"Citations:\s*(.*?)(?=\nConfidence:|\nLimitation:|$)", raw_response, re.DOTALL)
            conf_match = re.search(r"Confidence:\s*(High|Medium|Low)", raw_response, re.IGNORECASE)

            answer = ans_match.group(1).strip() if ans_match else raw_response
            raw_cites = cite_match.group(1).strip() if cite_match else ""
            citations = re.findall(r"\[.*?\]", raw_cites)
            confidence = conf_match.group(1).capitalize() if conf_match else "Medium"
        else:
            answer, citations, confidence = self._deterministic_extractive_answer(user_question, retrieved)

        # Post-check verification
        passed, verified_conf, valid_cites = self.post_check_verification(answer, citations, retrieved)
        if not passed:
            confidence = "Low"
        citations = valid_cites if valid_cites else citations

        self._log_audit_entry(user_question, version_filter, retrieved, answer, citations, confidence, passed, user)

        return {
            "query": user_question,
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "limitation_note": "Advisory output. Requires engineer review.",
            "post_check_passed": passed,
            "retrieved_chunks": retrieved
        }


def main():
    pipeline = AUTOSARRAGPipeline()
    sample_queries = [
        ("What happens to door locks when a crash pulse is detected?", "v1"),
        ("What is the auto-lock speed threshold?", "v1"),
        ("What is the data type of VehicleSpeedKmh in v2?", "v2"),
        ("What is the turbocharger boost pressure?", "v1")  # Unanswerable
    ]

    print("=" * 70)
    print("STEP 4: RAG Pipeline Execution & Smoke Verification")
    print("=" * 70)

    for q, ver in sample_queries:
        print(f"\n[QUERY]: {q} (Target Version: {ver})")
        res = pipeline.query(q, version_filter=ver)
        print(f"  Answer:     {res['answer']}")
        print(f"  Citations:  {', '.join(res['citations']) if res['citations'] else 'None'}")
        print(f"  Confidence: {res['confidence']}")
        print(f"  Post-Check: {'PASSED' if res['post_check_passed'] else 'FAILED'}")
        print(f"  Notice:     {res['limitation_note']}")


if __name__ == "__main__":
    main()
