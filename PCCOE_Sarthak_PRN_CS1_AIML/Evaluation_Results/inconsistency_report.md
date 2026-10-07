# AUTOSAR HLD Architecture Revision Inconsistency Report

> **NOTICE:** AI-assisted analysis output. Advisory findings require senior engineer review before architecture governance sign-off.

## 1. Executive Summary
- **Baseline Specification:** `HLD_BodyControl_v1.pdf`
- **Revised Specification:** `HLD_BodyControl_v2.pdf`
- **Total Inconsistencies Detected:** **6**

### Findings by Category
| Category | Detected Count | Default Severity |
| :--- | :---: | :--- |
| Renamed Signal | 2 | **High** |
| Removed Port | 1 | **Critical** |
| Changed Data Type | 1 | **High** |
| Referenced But Undefined Component | 1 | **High** |
| Interface With No Consumer | 1 | **Medium** |

## 2. Detailed Inconsistency Findings & Citations

### INC-SIG-01: Renamed Signal - `Sig_DoorState_FrontLeft`
- **Severity:** `High`
- **Citation:** [HLD_BodyControl, v2, page 8, Section 6.1 (Signal List)]
- **Baseline (v1) Value:** `Sig_DoorState_FrontLeft`
- **Revised (v2) Value:** `Sig_DoorState_FL_Status`
- **Architectural Impact:** Signal 'Sig_DoorState_FrontLeft' was renamed to 'Sig_DoorState_FL_Status' in v2 without updating network communication bridges or defining an RTE alias.

### INC-SIG-02: Renamed Signal - `Sig_HeadlampStatus`
- **Severity:** `High`
- **Citation:** [HLD_BodyControl, v2, page 8, Section 6.1 (Signal List)]
- **Baseline (v1) Value:** `Sig_HeadlampStatus`
- **Revised (v2) Value:** `Sig_ExteriorHeadlamp_State`
- **Architectural Impact:** Signal 'Sig_HeadlampStatus' was renamed to 'Sig_ExteriorHeadlamp_State' in v2 without updating network communication bridges or defining an RTE alias.

### INC-PORT-03: Removed Port - `DoorLockSWC::p_DoorLockStatus`
- **Severity:** `Critical`
- **Citation:** [HLD_BodyControl, v2, page 9, Section 7.1 (Component Port Bindings)]
- **Baseline (v1) Value:** `p_DoorLockStatus (If_DoorLockStatus)`
- **Revised (v2) Value:** `Removed`
- **Architectural Impact:** Provided Port 'p_DoorLockStatus' was removed from 'DoorLockSWC', breaking downstream receiver bindings.

### INC-TYPE-04: Changed Data Type - `If_VehicleSpeed::VehicleSpeedKmh`
- **Severity:** `High`
- **Citation:** [HLD_BodyControl, v2, page 6, Section 5.1 (S/R Interfaces)]
- **Baseline (v1) Value:** `Uint16`
- **Revised (v2) Value:** `Float32`
- **Architectural Impact:** Data element 'VehicleSpeedKmh' in interface 'If_VehicleSpeed' changed type from 'Uint16' to 'Float32', causing RTE buffer incompatible sizing.

### INC-UNDEF-05: Referenced But Undefined Component - `SunroofCtrlSWC`
- **Severity:** `High`
- **Citation:** [HLD_BodyControl, v2, page 5, Section 4.2 (Auxiliary System Dependencies)]
- **Baseline (v1) Value:** `Not Referenced`
- **Revised (v2) Value:** `Referenced on Page 5`
- **Architectural Impact:** Component 'SunroofCtrlSWC' is referenced in operational narrative text on Page 5, but does not exist in the formal AUTOSAR component inventory table.

### INC-ORPHAN-06: Interface With No Consumer - `If_TrailerHitchDetect`
- **Severity:** `Medium`
- **Citation:** [HLD_BodyControl, v2, page 6, Section 5.1 (S/R Interfaces)]
- **Baseline (v1) Value:** `Not Present`
- **Revised (v2) Value:** `Provided but Unconnected`
- **Architectural Impact:** Interface 'If_TrailerHitchDetect' is declared in the interface catalog but has no matching receiver port in any application component.
