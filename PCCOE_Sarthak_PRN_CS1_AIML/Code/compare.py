#!/usr/bin/env python3
"""
Revision Comparison Module (v1 vs v2) for AUTOSAR HLD Documents
Performs:
1. Deterministic diffing of components, interfaces, ports, and signals.
2. Rule-based architecture defect detection:
   - Renamed signals without interface alias
   - Removed ports breaking coupling
   - Changed data types causing RTE buffer mismatch
   - Referenced-but-undefined components (e.g. SunroofCtrlSWC)
   - Interfaces with no consumer (e.g. If_TrailerHitchDetect)
3. Severity classification and exact page-level citations.
4. Export to JSON and Markdown reports.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from extract_entities import AUTOSAREntityExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AUTOSAR_Compare")

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DATA_DIR = BASE_DIR / "Input_Data"
EVAL_RESULTS_DIR = BASE_DIR / "Evaluation_Results"
EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class AUTOSARRevisionComparator:
    def __init__(self):
        self.extractor = AUTOSAREntityExtractor()

    def compare_revisions(self, v1_pdf_path: str, v2_pdf_path: str) -> Dict[str, Any]:
        """Runs deterministic rule-based comparison between v1 and v2 specifications."""
        logger.info("Extracting entities from baseline v1...")
        ent_v1 = self.extractor.extract_from_pdf(v1_pdf_path, version="v1")
        logger.info("Extracting entities from revision v2...")
        ent_v2 = self.extractor.extract_from_pdf(v2_pdf_path, version="v2")

        inconsistencies = []

        # ================= CHECK 1: SIGNAL DIFF & RENAMING =================
        v1_sigs = {s["signal_name"]: s for s in ent_v1["signals"]}
        v2_sigs = {s["signal_name"]: s for s in ent_v2["signals"]}

        # Heuristic matching for renamed signals: same bus, same cycle, similar name or endpoints
        for s1_name, s1_data in v1_sigs.items():
            if s1_name not in v2_sigs:
                best_match = None
                for s2_name, s2_data in v2_sigs.items():
                    if s2_name not in v1_sigs:
                        # If bus, source, and destination match, or names share prefix
                        if (s1_data["bus"] == s2_data["bus"] and
                            s1_data["source_swc"] == s2_data["source_swc"] and
                            s1_data["destination_swc"] == s2_data["destination_swc"]):
                            best_match = s2_name
                            break
                        elif s1_name[:8] == s2_name[:8]:
                            best_match = s2_name
                            break

                if best_match:
                    inconsistencies.append({
                        "id": f"INC-SIG-{len(inconsistencies)+1:02d}",
                        "category": "Renamed Signal",
                        "severity": "High",
                        "entity": s1_name,
                        "v1_value": s1_name,
                        "v2_value": best_match,
                        "page_v1": s1_data["source_page"],
                        "page_v2": v2_sigs[best_match]["source_page"],
                        "citation": f"[HLD_BodyControl, v2, page {v2_sigs[best_match]['source_page']}, Section 6.1 (Signal List)]",
                        "explanation": f"Signal '{s1_name}' was renamed to '{best_match}' in v2 without updating network communication bridges or defining an RTE alias."
                    })
                else:
                    inconsistencies.append({
                        "id": f"INC-SIG-{len(inconsistencies)+1:02d}",
                        "category": "Removed Signal",
                        "severity": "Medium",
                        "entity": s1_name,
                        "v1_value": s1_name,
                        "v2_value": "None (Removed)",
                        "page_v1": s1_data["source_page"],
                        "page_v2": 8,
                        "citation": f"[HLD_BodyControl, v1, page {s1_data['source_page']}, Section 6.1]",
                        "explanation": f"Signal '{s1_name}' exists in v1 but is absent in v2 signal tables."
                    })

        # ================= CHECK 2: PORT & DEPENDENCY DIFF =================
        v1_deps = {d["component_name"]: d for d in ent_v1["dependencies"]}
        v2_deps = {d["component_name"]: d for d in ent_v2["dependencies"]}

        for c_name, v1_dep in v1_deps.items():
            if c_name in v2_deps:
                v2_dep = v2_deps[c_name]
                p1_ports = [p.strip() for p in v1_dep["provided_ports"].split(",") if p.strip()]
                p2_ports = [p.strip() for p in v2_dep["provided_ports"].split(",") if p.strip()]

                r1_ports = [p.strip() for p in v1_dep["required_ports"].split(",") if p.strip()]
                r2_ports = [p.strip() for p in v2_dep["required_ports"].split(",") if p.strip()]

                # Check removed provided ports
                for p in p1_ports:
                    if "[removed in v2]" in v2_dep["provided_ports"].lower() or (p not in p2_ports and not any(p[:8] in p2 for p2 in p2_ports)):
                        inconsistencies.append({
                            "id": f"INC-PORT-{len(inconsistencies)+1:02d}",
                            "category": "Removed Port",
                            "severity": "Critical",
                            "entity": f"{c_name}::{p.split(' ')[0]}",
                            "v1_value": p,
                            "v2_value": "Removed",
                            "page_v1": v1_dep["source_page"],
                            "page_v2": v2_dep["source_page"],
                            "citation": f"[HLD_BodyControl, v2, page {v2_dep['source_page']}, Section 7.1 (Component Port Bindings)]",
                            "explanation": f"Provided Port '{p.split(' ')[0]}' was removed from '{c_name}', breaking downstream receiver bindings."
                        })

                # Check removed required ports
                for p in r1_ports:
                    if p not in r2_ports and not any(p[:8] in p2 for p2 in r2_ports):
                        inconsistencies.append({
                            "id": f"INC-PORT-{len(inconsistencies)+1:02d}",
                            "category": "Removed Port",
                            "severity": "High",
                            "entity": f"{c_name}::{p.split(' ')[0]}",
                            "v1_value": p,
                            "v2_value": "Removed",
                            "page_v1": v1_dep["source_page"],
                            "page_v2": v2_dep["source_page"],
                            "citation": f"[HLD_BodyControl, v2, page {v2_dep['source_page']}, Section 7.1 (Component Port Bindings)]",
                            "explanation": f"Required Port '{p.split(' ')[0]}' was unmapped from '{c_name}', disabling incoming sensor input."
                        })

        # ================= CHECK 3: CHANGED DATA TYPES =================
        v1_ifs = {f"{i['interface_name']}::{i['data_element']}": i for i in ent_v1["interfaces"]}
        v2_ifs = {f"{i['interface_name']}::{i['data_element']}": i for i in ent_v2["interfaces"]}

        for key, if1 in v1_ifs.items():
            if key in v2_ifs:
                if2 = v2_ifs[key]
                if if1["data_type"] and if2["data_type"] and if1["data_type"] != if2["data_type"]:
                    inconsistencies.append({
                        "id": f"INC-TYPE-{len(inconsistencies)+1:02d}",
                        "category": "Changed Data Type",
                        "severity": "High",
                        "entity": key,
                        "v1_value": if1["data_type"],
                        "v2_value": if2["data_type"],
                        "page_v1": if1["source_page"],
                        "page_v2": if2["source_page"],
                        "citation": f"[HLD_BodyControl, v2, page {if2['source_page']}, Section 5.1 (S/R Interfaces)]",
                        "explanation": f"Data element '{if1['data_element']}' in interface '{if1['interface_name']}' changed type from '{if1['data_type']}' to '{if2['data_type']}', causing RTE buffer incompatible sizing."
                    })

        # ================= CHECK 4: REFERENCED BUT UNDEFINED COMPONENTS =================
        formal_comp_names = {c["component_name"] for c in ent_v2["components"] if c["extraction_method"] == "deterministic_table"}
        for c in ent_v2["components"]:
            if c["extraction_method"] == "text_heuristic" and c["component_name"] not in formal_comp_names:
                inconsistencies.append({
                    "id": f"INC-UNDEF-{len(inconsistencies)+1:02d}",
                    "category": "Referenced But Undefined Component",
                    "severity": "High",
                    "entity": c["component_name"],
                    "v1_value": "Not Referenced",
                    "v2_value": f"Referenced on Page {c['source_page']}",
                    "page_v1": 0,
                    "page_v2": c["source_page"],
                    "citation": f"[HLD_BodyControl, v2, page {c['source_page']}, Section 4.2 (Auxiliary System Dependencies)]",
                    "explanation": f"Component '{c['component_name']}' is referenced in operational narrative text on Page {c['source_page']}, but does not exist in the formal AUTOSAR component inventory table."
                })

        # ================= CHECK 5: INTERFACES WITH NO CONSUMER (ORPHANED) =================
        # Look for interfaces added in v2 that have no consumer in dependencies
        all_required_ports_text = " ".join([d.get("required_ports", "") for d in ent_v2["dependencies"]])
        for if_key, if_data in v2_ifs.items():
            if if_key not in v1_ifs:
                if_name = if_data["interface_name"]
                if if_name not in all_required_ports_text:
                    inconsistencies.append({
                        "id": f"INC-ORPHAN-{len(inconsistencies)+1:02d}",
                        "category": "Interface With No Consumer",
                        "severity": "Medium",
                        "entity": if_name,
                        "v1_value": "Not Present",
                        "v2_value": "Provided but Unconnected",
                        "page_v1": 0,
                        "page_v2": if_data["source_page"],
                        "citation": f"[HLD_BodyControl, v2, page {if_data['source_page']}, Section 5.1 (S/R Interfaces)]",
                        "explanation": f"Interface '{if_name}' is declared in the interface catalog but has no matching receiver port in any application component."
                    })

        logger.info(f"Comparison complete: Detected {len(inconsistencies)} architectural defects/inconsistencies.")

        return {
            "baseline_document": Path(v1_pdf_path).name,
            "revised_document": Path(v2_pdf_path).name,
            "total_defects_detected": len(inconsistencies),
            "summary_by_category": {
                "Renamed Signal": len([i for i in inconsistencies if i["category"] == "Renamed Signal"]),
                "Removed Port": len([i for i in inconsistencies if i["category"] == "Removed Port"]),
                "Changed Data Type": len([i for i in inconsistencies if i["category"] == "Changed Data Type"]),
                "Referenced But Undefined Component": len([i for i in inconsistencies if i["category"] == "Referenced But Undefined Component"]),
                "Interface With No Consumer": len([i for i in inconsistencies if i["category"] == "Interface With No Consumer"]),
            },
            "inconsistencies": inconsistencies
        }

    def generate_markdown_report(self, report_data: Dict[str, Any], output_path: Path) -> Path:
        """Renders structured Markdown report with severity tags and citations."""
        md_lines = [
            "# AUTOSAR HLD Architecture Revision Inconsistency Report",
            "",
            "> **NOTICE:** AI-assisted analysis output. Advisory findings require senior engineer review before architecture governance sign-off.",
            "",
            "## 1. Executive Summary",
            f"- **Baseline Specification:** `{report_data['baseline_document']}`",
            f"- **Revised Specification:** `{report_data['revised_document']}`",
            f"- **Total Inconsistencies Detected:** **{report_data['total_defects_detected']}**",
            "",
            "### Findings by Category",
            "| Category | Detected Count | Default Severity |",
            "| :--- | :---: | :--- |"
        ]

        for cat, cnt in report_data["summary_by_category"].items():
            sev = "Critical" if "Port" in cat else ("High" if "Type" in cat or "Undefined" in cat or "Signal" in cat else "Medium")
            md_lines.append(f"| {cat} | {cnt} | **{sev}** |")

        md_lines.extend([
            "",
            "## 2. Detailed Inconsistency Findings & Citations",
            ""
        ])

        for inc in report_data["inconsistencies"]:
            md_lines.extend([
                f"### {inc['id']}: {inc['category']} - `{inc['entity']}`",
                f"- **Severity:** `{inc['severity']}`",
                f"- **Citation:** {inc['citation']}",
                f"- **Baseline (v1) Value:** `{inc['v1_value']}`",
                f"- **Revised (v2) Value:** `{inc['v2_value']}`",
                f"- **Architectural Impact:** {inc['explanation']}",
                ""
            ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines).strip() + "\n")
        return output_path


def main():
    v1_pdf = INPUT_DATA_DIR / "HLD_BodyControl_v1.pdf"
    v2_pdf = INPUT_DATA_DIR / "HLD_BodyControl_v2.pdf"

    if not v1_pdf.exists() or not v2_pdf.exists():
        print(f"Error: Missing synthetic PDFs in {INPUT_DATA_DIR}")
        sys.exit(1)

    comparator = AUTOSARRevisionComparator()
    print("=" * 70)
    print("STEP 6: Revision Comparison (v1 vs v2 Inconsistency Detection)")
    print("=" * 70)

    report = comparator.compare_revisions(str(v1_pdf), str(v2_pdf))

    json_out = EVAL_RESULTS_DIR / "inconsistency_report.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md_out = EVAL_RESULTS_DIR / "inconsistency_report.md"
    comparator.generate_markdown_report(report, md_out)

    print(f"\n[REPORT SUMMARY]: Detected {report['total_defects_detected']} inconsistencies:")
    for cat, cnt in report["summary_by_category"].items():
        print(f"  • {cat}: {cnt}")
    print(f"\n[SAVED]: {json_out.name} & {md_out.name} in Evaluation_Results/")


if __name__ == "__main__":
    main()
