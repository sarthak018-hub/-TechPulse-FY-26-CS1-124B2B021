#!/usr/bin/env python3
"""
PDF Ingestion Module for AUTOSAR HLD Documents
Parses text, headings, tables, and page metadata using PyMuPDF and pdfplumber.
Validates file integrity, version tags, and outputs structured section maps.
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
import pdfplumber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AUTOSAR_Ingest")


class DocumentIngestionError(Exception):
    """Raised when document validation or parsing fails."""
    pass


class AUTOSARDocumentIngester:
    def __init__(self, doc_id: str = "HLD_BodyControl"):
        self.doc_id = doc_id

    def validate_document(self, file_path: Path, expected_version: str) -> None:
        """Validates file existence, non-zero size, extension, and version tag."""
        if not file_path.exists():
            raise DocumentIngestionError(f"Target file does not exist: {file_path}")
        if file_path.suffix.lower() != ".pdf":
            raise DocumentIngestionError(f"Invalid file type: {file_path.suffix}. Expected .pdf")
        if file_path.stat().st_size == 0:
            raise DocumentIngestionError(f"Target file is empty (0 bytes): {file_path}")

        # Validate version tag in file name or parameter
        norm_ver = expected_version.lower().strip()
        if norm_ver not in ["v1", "v2"]:
            raise DocumentIngestionError(f"Invalid version tag '{expected_version}'. Must be 'v1' or 'v2'.")

        logger.info(f"Document validated successfully: {file_path.name} ({file_path.stat().st_size / 1024:.1f} KB, version={norm_ver})")

    def _extract_headings_and_sections(self, text: str) -> List[Dict[str, str]]:
        """Splits raw page text into distinct section blocks using heading heuristics."""
        lines = text.split("\n")
        sections = []
        curr_heading = "General"
        curr_lines = []

        # Regex for section headings like "1. Introduction", "Section 0.1", "5.1 Sender-Receiver"
        heading_pattern = re.compile(r"^(\d+(\.\d+)*\s+[A-Z][A-Za-z0-9\s\-/&()]+|Section\s+\d+(\.\d+)*:?\s+.*)$")

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Skip running headers and footers
            if "AUTOSAR High-Level Design" in line_clean or "Page " in line_clean and " of " in line_clean:
                continue
            if "Advisory Document" in line_clean or "Baseline Architecture" in line_clean:
                continue

            if heading_pattern.match(line_clean) and len(line_clean) < 100:
                if curr_lines:
                    sections.append({
                        "section_title": curr_heading,
                        "content": "\n".join(curr_lines).strip()
                    })
                    curr_lines = []
                curr_heading = line_clean
            else:
                curr_lines.append(line_clean)

        if curr_lines:
            sections.append({
                "section_title": curr_heading,
                "content": "\n".join(curr_lines).strip()
            })

        return sections

    def _extract_tables(self, pdfplumber_page) -> List[List[List[str]]]:
        """Extracts structured tabular data from a page via pdfplumber."""
        tables = []
        raw_tables = pdfplumber_page.extract_tables()
        for t in raw_tables:
            cleaned_table = []
            for row in t:
                cleaned_row = [str(cell).strip().replace("\n", " ") if cell is not None else "" for cell in row]
                if any(cleaned_row):
                    cleaned_table.append(cleaned_row)
            if cleaned_table:
                tables.append(cleaned_table)
        return tables

    def ingest_pdf(self, file_path: str, version: str) -> Dict[str, Any]:
        """Performs full ingestion of an AUTOSAR HLD PDF."""
        path = Path(file_path).resolve()
        self.validate_document(path, version)

        logger.info(f"Starting parsing for {path.name}...")
        parsed_doc = {
            "doc_id": self.doc_id,
            "version": version.lower(),
            "file_name": path.name,
            "file_size_bytes": path.stat().st_size,
            "total_pages": 0,
            "pages": []
        }

        with fitz.open(path) as doc_fitz, pdfplumber.open(path) as doc_plumber:
            num_pages = len(doc_fitz)
            parsed_doc["total_pages"] = num_pages

            for page_idx in range(num_pages):
                page_num = page_idx + 1
                page_fitz = doc_fitz[page_idx]
                page_plumber = doc_plumber.pages[page_idx]

                # 1. Extract plain text
                raw_text = page_fitz.get_text("text")

                # 2. Extract structured sections
                sections = self._extract_headings_and_sections(raw_text)

                # 3. Extract tables
                tables = self._extract_tables(page_plumber)

                # 4. Classify primary content type
                if tables:
                    primary_type = "table"
                elif "Flow " in raw_text or "Execution Steps" in raw_text:
                    primary_type = "flow"
                else:
                    primary_type = "text"

                page_record = {
                    "page_number": page_num,
                    "content_type": primary_type,
                    "raw_text": raw_text.strip(),
                    "sections": sections,
                    "tables": tables,
                    "table_count": len(tables)
                }
                parsed_doc["pages"].append(page_record)
                logger.debug(f"Parsed Page {page_num}/{num_pages}: {len(sections)} sections, {len(tables)} tables")

        logger.info(f"[SUCCESS] Ingested {parsed_doc['total_pages']} pages from {path.name}")
        return parsed_doc


def main():
    if len(sys.argv) < 3:
        print("Usage: python Code/ingest.py <path_to_pdf> <version>")
        print("Example: python Code/ingest.py Input_Data/HLD_BodyControl_v1.pdf v1")
        sys.exit(1)

    pdf_path = sys.argv[1]
    version = sys.argv[2]
    ingester = AUTOSARDocumentIngester()
    result = ingester.ingest_pdf(pdf_path, version)

    out_file = Path(pdf_path).parent / f"ingested_{result['doc_id']}_{version}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"[INFO] Ingested data written to: {out_file.name}")


if __name__ == "__main__":
    main()
