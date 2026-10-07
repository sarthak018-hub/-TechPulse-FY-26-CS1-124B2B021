#!/usr/bin/env python3
"""
Entity Extraction Module for AUTOSAR HLD Documents
Extracts:
- Components (Name, Type, ASIL, Period, Description, Source Page)
- Interfaces (Name, Type, Elements, Data Type, Unit, Source Page)
- Signals (Name, Type, Cycle Time, Bus, Source SWC, Dest SWC, Source Page)
- Dependencies (Component, Provided Ports, Required Ports, Source Page)

Methodology:
1. Deterministic table parsing first.
2. Text regex / heuristic extraction second.
3. Merge and deduplicate.
4. Export structured JSON and CSV.
"""

import os
import sys
import json
import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from ingest import AUTOSARDocumentIngester

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AUTOSAR_EntityExtractor")

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DATA_DIR = BASE_DIR / "Input_Data"


class AUTOSAREntityExtractor:
    def __init__(self):
        self.ingester = AUTOSARDocumentIngester()

    def extract_from_pdf(self, pdf_path: str, version: str) -> Dict[str, Any]:
        """Runs two-stage deterministic table and text extraction from an HLD PDF."""
        path = Path(pdf_path).resolve()
        logger.info(f"Extracting entities from {path.name} (version={version})...")
        parsed_doc = self.ingester.ingest_pdf(str(path), version=version)

        components = []
        interfaces = []
        signals = []
        dependencies = []

        seen_comp_names = set()
        seen_if_names = set()
        seen_sig_names = set()

        # ================= STAGE 1: DETERMINISTIC TABLE PARSING =================
        for page in parsed_doc["pages"]:
            page_num = page["page_number"]
            tables = page.get("tables", [])

            for table in tables:
                if not table or len(table) < 2:
                    continue
                header = [h.lower() for h in table[0]]

                # 1. Component Table detection
                if any("component name" in h or "swc name" in h for h in header):
                    name_idx = next(i for i, h in enumerate(header) if "component" in h or "swc" in h)
                    type_idx = next((i for i, h in enumerate(header) if "type" in h), -1)
                    asil_idx = next((i for i, h in enumerate(header) if "asil" in h), -1)
                    period_idx = next((i for i, h in enumerate(header) if "period" in h), -1)
                    desc_idx = next((i for i, h in enumerate(header) if "description" in h or "function" in h), -1)

                    for row in table[1:]:
                        if len(row) > name_idx and row[name_idx].strip():
                            c_name = row[name_idx].strip()
                            if c_name not in seen_comp_names:
                                components.append({
                                    "component_name": c_name,
                                    "type": row[type_idx].strip() if type_idx != -1 and len(row) > type_idx else "Application",
                                    "asil": row[asil_idx].strip() if asil_idx != -1 and len(row) > asil_idx else "QM",
                                    "period": row[period_idx].strip() if period_idx != -1 and len(row) > period_idx else "N/A",
                                    "description": row[desc_idx].strip() if desc_idx != -1 and len(row) > desc_idx else "",
                                    "source_page": page_num,
                                    "extraction_method": "deterministic_table"
                                })
                                seen_comp_names.add(c_name)

                # 2. Interface Table detection (S/R or C/S)
                elif any("interface name" in h for h in header):
                    if_name_idx = next(i for i, h in enumerate(header) if "interface" in h)
                    elem_idx = next((i for i, h in enumerate(header) if "element" in h or "operation" in h), -1)
                    dtype_idx = next((i for i, h in enumerate(header) if "data type" in h or "argument" in h), -1)
                    unit_idx = next((i for i, h in enumerate(header) if "unit" in h or "return" in h), -1)

                    for row in table[1:]:
                        if len(row) > if_name_idx and row[if_name_idx].strip():
                            i_name = row[if_name_idx].strip()
                            elem = row[elem_idx].strip() if elem_idx != -1 and len(row) > elem_idx else ""
                            key = f"{i_name}::{elem}"
                            if key not in seen_if_names:
                                if_type = "Client-Server" if ("operation" in " ".join(header) or "(" in elem) else "Sender-Receiver"
                                interfaces.append({
                                    "interface_name": i_name,
                                    "type": if_type,
                                    "data_element": elem,
                                    "data_type": row[dtype_idx].strip() if dtype_idx != -1 and len(row) > dtype_idx else "",
                                    "unit": row[unit_idx].strip() if unit_idx != -1 and len(row) > unit_idx else "",
                                    "source_page": page_num,
                                    "extraction_method": "deterministic_table"
                                })
                                seen_if_names.add(key)

                # 3. Signal Table detection
                elif any("signal name" in h for h in header):
                    sig_idx = next(i for i, h in enumerate(header) if "signal" in h)
                    type_idx = next((i for i, h in enumerate(header) if "type" in h), -1)
                    cycle_idx = next((i for i, h in enumerate(header) if "cycle" in h), -1)
                    bus_idx = next((i for i, h in enumerate(header) if "bus" in h), -1)
                    src_idx = next((i for i, h in enumerate(header) if "source" in h), -1)
                    dst_idx = next((i for i, h in enumerate(header) if "destination" in h), -1)

                    for row in table[1:]:
                        if len(row) > sig_idx and row[sig_idx].strip():
                            s_name = row[sig_idx].strip()
                            if s_name not in seen_sig_names:
                                signals.append({
                                    "signal_name": s_name,
                                    "data_type": row[type_idx].strip() if type_idx != -1 and len(row) > type_idx else "",
                                    "cycle_time": row[cycle_idx].strip() if cycle_idx != -1 and len(row) > cycle_idx else "",
                                    "bus": row[bus_idx].strip() if bus_idx != -1 and len(row) > bus_idx else "",
                                    "source_swc": row[src_idx].strip() if src_idx != -1 and len(row) > src_idx else "",
                                    "destination_swc": row[dst_idx].strip() if dst_idx != -1 and len(row) > dst_idx else "",
                                    "source_page": page_num,
                                    "extraction_method": "deterministic_table"
                                })
                                seen_sig_names.add(s_name)

                # 4. Dependency / Port Binding Table detection
                elif any("provided ports" in h or "pport" in h for h in header):
                    swc_idx = next(i for i, h in enumerate(header) if "component" in h or "swc" in h)
                    pport_idx = next((i for i, h in enumerate(header) if "provided" in h or "pport" in h), -1)
                    rport_idx = next((i for i, h in enumerate(header) if "required" in h or "rport" in h), -1)

                    for row in table[1:]:
                        if len(row) > swc_idx and row[swc_idx].strip():
                            c_name = row[swc_idx].strip()
                            dependencies.append({
                                "component_name": c_name,
                                "provided_ports": row[pport_idx].strip() if pport_idx != -1 and len(row) > pport_idx else "",
                                "required_ports": row[rport_idx].strip() if rport_idx != -1 and len(row) > rport_idx else "",
                                "source_page": page_num,
                                "extraction_method": "deterministic_table"
                            })

        # ================= STAGE 2: TEXT HEURISTIC PARSING =================
        # Scans for referenced components that may be absent from formal tables (e.g. SunroofCtrlSWC in v2)
        for page in parsed_doc["pages"]:
            page_num = page["page_number"]
            raw_text = page.get("raw_text", "")

            # Regex search for SWC identifiers: e.g. SunroofCtrlSWC, TirePressureBridgeSWC
            text_swcs = set(re.findall(r"\b([A-Z][a-zA-Z0-9]+SWC)\b", raw_text))
            for swc in text_swcs:
                if swc not in seen_comp_names:
                    logger.info(f"Found component referenced in text: {swc} (Page {page_num})")
                    components.append({
                        "component_name": swc,
                        "type": "Referenced In Text",
                        "asil": "Unspecified",
                        "period": "Unspecified",
                        "description": f"Referenced in Section text on Page {page_num}; missing from component table.",
                        "source_page": page_num,
                        "extraction_method": "text_heuristic"
                    })
                    seen_comp_names.add(swc)

        logger.info(f"Extracted {len(components)} components, {len(interfaces)} interfaces, {len(signals)} signals, {len(dependencies)} dependency records.")

        return {
            "doc_id": parsed_doc["doc_id"],
            "version": version.lower(),
            "summary": {
                "total_components": len(components),
                "total_interfaces": len(interfaces),
                "total_signals": len(signals),
                "total_dependencies": len(dependencies)
            },
            "components": components,
            "interfaces": interfaces,
            "signals": signals,
            "dependencies": dependencies
        }

    def export_results(self, data: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
        """Exports extracted entity catalogs to JSON and CSV formats."""
        output_dir.mkdir(parents=True, exist_ok=True)
        ver = data["version"]
        doc_id = data["doc_id"]
        created_files = {}

        # 1. Master JSON
        json_path = output_dir / f"extracted_entities_{doc_id}_{ver}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        created_files["json"] = str(json_path)

        # 2. Components CSV
        comp_csv = output_dir / f"extracted_components_{ver}.csv"
        if data["components"]:
            with open(comp_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(data["components"][0].keys()))
                writer.writeheader()
                writer.writerows(data["components"])
            created_files["components_csv"] = str(comp_csv)

        # 3. Interfaces CSV
        if_csv = output_dir / f"extracted_interfaces_{ver}.csv"
        if data["interfaces"]:
            with open(if_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(data["interfaces"][0].keys()))
                writer.writeheader()
                writer.writerows(data["interfaces"])
            created_files["interfaces_csv"] = str(if_csv)

        # 4. Signals CSV
        sig_csv = output_dir / f"extracted_signals_{ver}.csv"
        if data["signals"]:
            with open(sig_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(data["signals"][0].keys()))
                writer.writeheader()
                writer.writerows(data["signals"])
            created_files["signals_csv"] = str(sig_csv)

        # 5. Dependencies CSV
        dep_csv = output_dir / f"extracted_dependencies_{ver}.csv"
        if data["dependencies"]:
            with open(dep_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(data["dependencies"][0].keys()))
                writer.writeheader()
                writer.writerows(data["dependencies"])
            created_files["dependencies_csv"] = str(dep_csv)

        return created_files


def main():
    extractor = AUTOSAREntityExtractor()
    input_dir = INPUT_DATA_DIR

    print("=" * 70)
    print("STEP 5: Entity Extraction Execution (Components, Interfaces, Signals)")
    print("=" * 70)

    # Process v1
    v1_pdf = input_dir / "HLD_BodyControl_v1.pdf"
    if v1_pdf.exists():
        data_v1 = extractor.extract_from_pdf(str(v1_pdf), version="v1")
        files_v1 = extractor.export_results(data_v1, input_dir)
        print(f"\n[V1 EXTRACTION]: {data_v1['summary']}")
        print(f"  Exported: {', '.join([Path(p).name for p in files_v1.values()])}")

    # Process v2
    v2_pdf = input_dir / "HLD_BodyControl_v2.pdf"
    if v2_pdf.exists():
        data_v2 = extractor.extract_from_pdf(str(v2_pdf), version="v2")
        files_v2 = extractor.export_results(data_v2, input_dir)
        print(f"\n[V2 EXTRACTION]: {data_v2['summary']}")
        print(f"  Exported: {', '.join([Path(p).name for p in files_v2.values()])}")


if __name__ == "__main__":
    main()
