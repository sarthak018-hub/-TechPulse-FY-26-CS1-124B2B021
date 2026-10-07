# Data Sources and Synthetic Generation Declaration

## 1. Provenance Statement
All architectural design documents, interface catalogues, component tables, signal matrices, and diagnostic definitions contained in this directory (`Input_Data/`) are **100% synthetic**. They were programmatically generated specifically for academic research, engineering education, and evaluation.

- **Author / Lab:** PCCOE Department of Computer Engineering / AI & ML Lab (Pune)
- **Generator Script:** `Code/generate_synthetic_data.py`
- **Random Seed:** `42` (Fixed seed for deterministic, 100% reproducible builds)
- **Generation Framework:** Python 3.11 with ReportLab 4.1.0

## 2. No Confidential Information
No proprietary, confidential, restricted, or trade-secret documents from any automotive OEM or Tier-1 supplier were used, copied, or referenced. The components, interfaces, and pinouts represent generalized Classic AUTOSAR 4.4 architectural patterns created purely for academic analysis.

## 3. Dataset Summary
| File | Type | Purpose | Size / Pages |
| :--- | :--- | :--- | :--- |
| `HLD_BodyControl_v1.pdf` | Document | Baseline architecture specification | 14 pages (Full text, 10 SWCs, tables) |
| `HLD_BodyControl_v2.pdf` | Document | Revised specification with seeded defects | 14 pages (5 seeded changes for diff testing) |
| `seeded_defects_ground_truth.json` | JSON | Ground truth defect catalog with exact pages | 6 verified defect annotations (5 categories) |

## 4. License and Terms of Use
This synthetic dataset is open for educational, benchmarking, and project assessment purposes under the **MIT License**.
