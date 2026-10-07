#!/usr/bin/env python3
"""
Unit and Integration Test Suite for AUTOSAR HLD Analysis Assistant
Verifies:
1. Section-aware chunking and Markdown table formatting
2. Metadata enrichment per chunk
3. Citation post-check validation and groundedness checks
4. Dual-gate refusal mechanism on out-of-domain questions
5. Deterministic architectural revision comparison rules
"""

import os
import sys
import pytest
from pathlib import Path

# Add Code directory to system path
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from chunk_embed import SectionAwareChunker
from rag import AUTOSARRAGPipeline
from compare import AUTOSARRevisionComparator


class TestChunkingPipeline:
    """Tests section-aware chunking and table formatting logic."""

    def test_chunk_creation_and_metadata(self):
        chunker = SectionAwareChunker(target_chunk_size=400, chunk_overlap=50)
        parsed_doc = {
            "doc_id": "TEST_DOC",
            "version": "v1.0",
            "total_pages": 1,
            "pages": [
                {
                    "page_number": 1,
                    "sections": [
                        {
                            "section_title": "1. Introduction",
                            "content": "This is an introductory section describing the AUTOSAR Body Control Module architecture in detail."
                        }
                    ],
                    "tables": []
                }
            ]
        }
        chunks = chunker.chunk_document(parsed_doc)
        assert len(chunks) > 0
        chunk = chunks[0]
        meta = chunk["metadata"]
        assert meta["doc_id"] == "TEST_DOC"
        assert meta["version"] == "v1.0"
        assert meta["page"] == 1
        assert meta["section"] == "1. Introduction"
        assert meta["chunk_type"] == "text"
        assert "AUTOSAR Body Control Module" in chunk["text"]

    def test_table_markdown_conversion(self):
        chunker = SectionAwareChunker(target_chunk_size=500, chunk_overlap=50)
        parsed_doc = {
            "doc_id": "TEST_DOC",
            "version": "v1.0",
            "total_pages": 1,
            "pages": [
                {
                    "page_number": 5,
                    "sections": [
                        {"section_title": "4.1 Software Component Table", "content": "Table description"}
                    ],
                    "tables": [
                        [
                            ["Component", "Type", "ASIL", "Period"],
                            ["DoorLockSWC", "Application", "ASIL-B", "20 ms"],
                            ["WindowCtrlSWC", "Application", "ASIL-A", "20 ms"]
                        ]
                    ]
                }
            ]
        }
        chunks = chunker.chunk_document(parsed_doc)
        table_chunks = [c for c in chunks if c["metadata"]["chunk_type"] == "table"]
        assert len(table_chunks) > 0
        t_chunk = table_chunks[0]
        assert "| Component | Type | ASIL | Period |" in t_chunk["text"]
        assert "| DoorLockSWC | Application | ASIL-B | 20 ms |" in t_chunk["text"]


class TestCitationAndRefusalGate:
    """Tests citation validator, groundedness checking, and refusal behavior."""

    @pytest.fixture(scope="class")
    def rag_pipeline(self):
        return AUTOSARRAGPipeline(top_k=4)

    def test_citation_post_check_valid(self, rag_pipeline):
        mock_retrieved = [
            {
                "chunk_id": "chunk_01",
                "text": "DoorLockSWC is classified as ASIL-B and operates cyclically at 20 ms.",
                "similarity": 0.85,
                "metadata": {
                    "doc_id": "HLD_BodyControl",
                    "version": "v1",
                    "page": 5,
                    "section": "4.1 SWC Inventory",
                    "chunk_type": "table"
                }
            }
        ]
        answer = "DoorLockSWC operates at 20 ms with ASIL-B rating."
        citations = ["[HLD_BodyControl, v1, page 5, 4.1 SWC Inventory]"]

        passed, conf, valid_cites = rag_pipeline.post_check_verification(answer, citations, mock_retrieved)
        assert passed is True
        assert conf == "High"
        assert len(valid_cites) == 1

    def test_citation_post_check_hallucinated_page_rejected(self, rag_pipeline):
        mock_retrieved = [
            {
                "chunk_id": "chunk_01",
                "text": "DoorLockSWC is classified as ASIL-B.",
                "similarity": 0.82,
                "metadata": {
                    "doc_id": "HLD_BodyControl",
                    "version": "v1",
                    "page": 5,
                    "section": "4.1 SWC Inventory",
                    "chunk_type": "table"
                }
            }
        ]
        answer = "Hallucinated statement claiming facts from page 99."
        citations = ["[HLD_BodyControl, v1, page 99, NonExistentSection]"]

        passed, conf, valid_cites = rag_pipeline.post_check_verification(answer, citations, mock_retrieved)
        assert passed is False
        assert conf == "Low"
        assert len(valid_cites) == 0

    def test_dual_gate_refusal_unanswerable_query(self, rag_pipeline):
        unanswerable_q = "What is the high-voltage traction inverter battery cooling pump PWM duty cycle?"
        res = rag_pipeline.query(unanswerable_q, version_filter="v1")

        assert "not found in the provided document" in res["answer"].lower()
        assert len(res["citations"]) == 0
        assert res["post_check_passed"] is True


class TestRevisionComparisonEngine:
    """Tests deterministic rule engine on seeded architectural defects."""

    @pytest.fixture(scope="class")
    def comparison_report(self):
        input_dir = CURRENT_DIR.parent / "Input_Data"
        v1_pdf = input_dir / "HLD_BodyControl_v1.pdf"
        v2_pdf = input_dir / "HLD_BodyControl_v2.pdf"
        comparator = AUTOSARRevisionComparator()
        return comparator.compare_revisions(str(v1_pdf), str(v2_pdf))

    def test_total_defects_detected(self, comparison_report):
        assert comparison_report["total_defects_detected"] >= 6
        findings = comparison_report["inconsistencies"]
        assert len(findings) >= 6

    def test_renamed_signal_detected(self, comparison_report):
        findings = [i for i in comparison_report["inconsistencies"] if i["category"] == "Renamed Signal"]
        assert len(findings) >= 2
        renamed_entities = [f["entity"] for f in findings]
        assert "Sig_DoorState_FrontLeft" in renamed_entities
        assert "Sig_HeadlampStatus" in renamed_entities

    def test_removed_port_detected(self, comparison_report):
        findings = [i for i in comparison_report["inconsistencies"] if i["category"] == "Removed Port"]
        assert len(findings) >= 1
        assert any("DoorLockSWC" in f["entity"] for f in findings)

    def test_changed_data_type_detected(self, comparison_report):
        findings = [i for i in comparison_report["inconsistencies"] if i["category"] == "Changed Data Type"]
        assert len(findings) >= 1
        assert any("VehicleSpeedKmh" in f["entity"] for f in findings)

    def test_referenced_undefined_component_detected(self, comparison_report):
        findings = [i for i in comparison_report["inconsistencies"] if i["category"] == "Referenced But Undefined Component"]
        assert len(findings) >= 1
        assert any("SunroofCtrlSWC" in f["entity"] for f in findings)

    def test_orphaned_interface_detected(self, comparison_report):
        findings = [i for i in comparison_report["inconsistencies"] if i["category"] == "Interface With No Consumer"]
        assert len(findings) >= 1
        assert any("If_TrailerHitchDetect" in f["entity"] for f in findings)
