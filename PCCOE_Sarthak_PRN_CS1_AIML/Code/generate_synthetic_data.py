#!/usr/bin/env python3
"""
Synthetic AUTOSAR HLD Document & Dataset Generator (14 Pages - 90-Minute Scope)
Produces:
1. HLD_BodyControl_v1.pdf (~14 pages, baseline)
2. HLD_BodyControl_v2.pdf (~14 pages, revision with 5 seeded changes)
3. seeded_defects_ground_truth.json
4. DATA_SOURCES.md
"""

import os
import json
import csv
import random
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.pdfgen import canvas

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DATA_DIR = BASE_DIR / "Input_Data"
INPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic running header and 'Page X of Y' footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        if self._pageNumber > 1:
            self.drawString(54, 802, "AUTOSAR High-Level Design: Body Control ECU (BCM)")
            doc_label = "ECN-2026-08 (Rev v2.0)" if getattr(self, "is_v2", False) else "Baseline Architecture (Rev v1.0)"
            self.drawRightString(541, 802, doc_label)
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 794, 541, 794)

            self.line(54, 48, 541, 48)
            self.drawString(54, 36, "Advisory Document - Engineering Review Required")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(541, 36, page_text)
        self.restoreState()


def build_pdf_document(output_path: Path, version: str = "v1"):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=colors.HexColor('#0f172a'), alignment=1, spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=12, leading=16,
        textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=20
    )
    meta_style = ParagraphStyle(
        'DocMeta', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=14,
        textColor=colors.HexColor('#334155'), alignment=1, spaceAfter=18
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=19,
        textColor=colors.HexColor('#1e293b'), spaceBefore=14, spaceAfter=8, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=colors.HexColor('#334155'), spaceBefore=10, spaceAfter=5, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=12.5,
        textColor=colors.HexColor('#1e293b'), spaceAfter=5
    )
    callout_style = ParagraphStyle(
        'Callout_Custom', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=8, leading=11.5,
        textColor=colors.HexColor('#0f766e'), backColor=colors.HexColor('#f0fdfa'),
        borderColor=colors.HexColor('#99f6e4'), borderWidth=0.5, borderPadding=5,
        spaceBefore=5, spaceAfter=6
    )
    table_cell = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#0f172a')
    )
    table_hdr = ParagraphStyle(
        'TableHdr', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white
    )

    story = []
    is_v2 = (version == "v2")
    version_title = "v2.0 (Engineering Change Notice ECN-2026-08)" if is_v2 else "v1.0 (Baseline Architecture Release)"

    # ================= PAGE 1: TITLE PAGE =================
    story.append(Spacer(1, 1.8 * inch))
    story.append(Paragraph("AUTOMOTIVE OPEN SYSTEM ARCHITECTURE (AUTOSAR)", ParagraphStyle('Brand', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0284c7'), alignment=1)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("High-Level Design Specification<br/>Body Control Module (BCM)", title_style))
    story.append(Paragraph(f"Document Identifier: SPEC-AUTOSAR-BCM-HLD-{version.upper()}<br/>Release Level: {version_title}", subtitle_style))
    story.append(Spacer(1, 20))

    meta_text = """
    <b>Project Title:</b> AUTOSAR HLD Document Analysis Assistant<br/>
    <b>Author:</b> Department of Computer Engineering / AI & ML Lab<br/>
    <b>Institution:</b> Pimpri Chinchwad College of Engineering (PCCOE), Pune<br/>
    <b>Classification:</b> Synthetic Architecture Data (Educational Model)<br/>
    <b>Date of Issue:</b> October 2026<br/>
    <b>Target Standard:</b> Classic AUTOSAR Release 4.4.0
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 40))

    disclaimer_text = """
    <b>NOTICE:</b> This High-Level Design document contains synthetic architectural models designed
    for automated retrieval, traceability validation, and inconsistency reporting. All components, ports,
    and signals comply with Classic AUTOSAR 4.4 methodology. Advisory output requires engineer review.
    """
    story.append(Paragraph(disclaimer_text, callout_style))
    story.append(PageBreak())

    # ================= PAGE 2: REVISION HISTORY & DOCUMENT CONTROL =================
    story.append(Paragraph("Document Control & Revision History", h1_style))
    story.append(Paragraph("Section 0.1: Change History Log", h2_style))
    rev_headers = ["Rev", "Date", "Author", "Change Description", "Approval Status"]
    rev_data = [
        [Paragraph(h, table_hdr) for h in rev_headers],
        [Paragraph("0.1", table_cell), Paragraph("2026-01-10", table_cell), Paragraph("Arch Team", table_cell), Paragraph("Initial draft structure and component boundaries", table_cell), Paragraph("Draft", table_cell)],
        [Paragraph("0.5", table_cell), Paragraph("2026-02-04", table_cell), Paragraph("Systems Lead", table_cell), Paragraph("Added Port/Interface tables and signal cycle times", table_cell), Paragraph("Reviewed", table_cell)],
        [Paragraph("1.0", table_cell), Paragraph("2026-03-15", table_cell), Paragraph("Chief Architect", table_cell), Paragraph("Formal baseline release v1.0. All 10 SWCs frozen.", table_cell), Paragraph("Approved", table_cell)],
    ]
    if is_v2:
        rev_data.append([
            Paragraph("2.0", table_cell), Paragraph("2026-08-20", table_cell), Paragraph("Systems Lead", table_cell),
            Paragraph("ECN-2026-08: Signal renaming, interface refactoring, and defect injection test revision.", table_cell),
            Paragraph("Pending Review", table_cell)
        ])
    rev_table = Table(rev_data, colWidths=[35, 65, 75, 230, 80])
    rev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(rev_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Section 0.2: Approvals & Signatures", h2_style))
    approval_data = [
        [Paragraph("Role", table_hdr), Paragraph("Name", table_hdr), Paragraph("Organization", table_hdr), Paragraph("Sign Date", table_hdr)],
        [Paragraph("Lead Systems Architect", table_cell), Paragraph("Dr. S. K. Kulkarni", table_cell), Paragraph("PCCOE Automotive Lab", table_cell), Paragraph("2026-03-16", table_cell)],
        [Paragraph("Safety Governance Lead", table_cell), Paragraph("Prof. V. Sharma", table_cell), Paragraph("Functional Safety Board", table_cell), Paragraph("2026-03-17", table_cell)],
        [Paragraph("Diagnostic Verification Lead", table_cell), Paragraph("Eng. R. Nair", table_cell), Paragraph("Validation Group", table_cell), Paragraph("2026-03-18", table_cell)],
    ]
    app_table = Table(approval_data, colWidths=[120, 120, 150, 95])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(app_table)
    story.append(PageBreak())

    # ================= PAGE 3: SECTION 1: INTRODUCTION & SCOPE =================
    story.append(Paragraph("1. Introduction and Architectural Scope", h1_style))
    story.append(Paragraph("1.1 Purpose of the High-Level Design", h2_style))
    p1_desc = """
    This High-Level Design (HLD) document defines the software architecture, component boundaries, port interfaces,
    signals, and interaction flows for the Body Control Module (BCM ECU).
    The BCM is responsible for managing core cabin functions including central door locking, power window automation,
    exterior lighting schemes, windshield wiper/washer cycles, immobilizer authentication, and diagnostic event recording.
    The architecture is formalized under Classic AUTOSAR Release 4.4.0 and targets deployment on a 32-bit automotive microcontroller
    with dual CAN-FD transceivers and a LIN sub-bus master controller.
    """
    story.append(Paragraph(p1_desc, body_style))

    story.append(Paragraph("1.2 System Scope & Operational Boundaries", h2_style))
    p1_scope = """
    The scope of this document encompasses all Application Software Components (Application SWCs) located above
    the AUTOSAR Runtime Environment (RTE). Basic Software (BSW) services such as the Diagnostic Event Manager (Dem),
    Diagnostic Communication Manager (Dcm), CAN State Manager (CanSM), and Operating System (OS) are referenced
    via standardized Service Ports and BSW bridges.
    <br/><br/>
    <b>In-Scope Functional Domains:</b>
    <br/>• Central Door Locking, child lock supervision, and crash-triggered emergency unlocking.
    <br/>• Smart Power Window control with express motion and anti-pinch safety algorithms.
    <br/>• Exterior Lighting (headlamps, turn signals, hazard lights) and ambient illumination.
    <br/>• Rain-sensing wiper intervals, high/low speed control, and washer fluid pump cycling.
    <br/>• Power state transitions between Active, Standby, and Low Voltage Sleep modes.
    <br/><br/>
    <b>Out-of-Scope Domains:</b>
    <br/>• Powertrain management, engine start sequence, and high-voltage battery charging.
    <br/>• Hardware PCB layout schematics and low-level MCAL register definitions.
    """
    story.append(Paragraph(p1_scope, body_style))

    story.append(Paragraph("1.3 Architectural Standards & Compliance", h2_style))
    p1_standards = """
    All software specifications in this document adhere to the following normative automotive standards:
    <br/>1. <b>AUTOSAR CP R4.4.0:</b> Component model, virtual function bus concepts, and standardized interface templates.
    <br/>2. <b>ISO 26262:2018:</b> Road Vehicles - Functional Safety (governing safety integrity levels up to ASIL-D).
    <br/>3. <b>ISO 14229-1 (UDS):</b> Unified Diagnostic Services on Controller Area Network.
    <br/>4. <b>ISO 11898-1/2:</b> Controller Area Network (CAN-FD) data link layer and physical transmission.
    """
    story.append(Paragraph(p1_standards, body_style))
    story.append(PageBreak())

    # ================= PAGE 4: SECTION 2: SYSTEM CONTEXT & HARDWARE BOUNDARY =================
    story.append(Paragraph("2. System Context and Hardware Boundary", h1_style))
    story.append(Paragraph("2.1 BCM Physical Context", h2_style))
    p2_ctx = """
    The BCM ECU acts as the primary gateway and actuator control center for vehicular body electronics.
    It interfaces directly with the central vehicle gateway over a 500 kbps / 2 Mbps CAN-FD network (Channel 1)
    and commands smart sub-actuators and sensors via a 19.2 kbps LIN sub-bus (Channel 0).
    <br/><br/>
    <b>Physical Transceivers & Interfaces:</b>
    <br/>• Dual high-speed CAN-FD transceivers supporting ISO 11898-2 with wake-up over bus capability.
    <br/>• Single-wire LIN master transceiver compliant with LIN 2.2A.
    <br/>• High-Side Smart Drivers (PROFET) for direct actuation of exterior lamps, wiper motors, and latch coils.
    <br/>• Configurable analog/digital input channels with low-pass hardware filtering for door switches.
    """
    story.append(Paragraph(p2_ctx, body_style))

    story.append(Paragraph("2.2 ECU Power Supply & Operating States", h2_style))
    p2_pwr = """
    The module operates under nominal 12V automotive battery voltage (operating range: 9.0V to 16.0V DC).
    Extended crank operating capability is maintained down to 6.0V DC for 500ms.
    Overvoltage protection isolates actuator stages when battery voltage exceeds 18.0V DC.
    <br/><br/>
    <b>Power Modes:</b>
    <br/>1. <b>RUN Mode (Active):</b> Microcontroller at 80 MHz, all SWC runnables executed periodically, full CAN/LIN transmission.
    <br/>2. <b>STANDBY Mode:</b> Core clock reduced to 8 MHz, actuators unpowered, CAN transceiver listening for network management frames.
    <br/>3. <b>SLEEP Mode:</b> Deep quiescent state (< 100 µA current draw), wake-up initiated only via keyless remote or door handle pull switch.
    """
    story.append(Paragraph(p2_pwr, body_style))

    story.append(Paragraph("2.3 Safety Concept & ASIL Allocation Matrix", h2_style))
    safety_data = [
        [Paragraph("Function / SWC", table_hdr), Paragraph("Hazard Scenario", table_hdr), Paragraph("Safety Goal", table_hdr), Paragraph("ASIL", table_hdr)],
        [Paragraph("DoorLockSWC", table_cell), Paragraph("Doors remain locked during collision", table_cell), Paragraph("Unlock all latches within 30ms of crash detection", table_cell), Paragraph("ASIL-B", table_cell)],
        [Paragraph("WindowCtrlSWC", table_cell), Paragraph("Pinch injury during automatic window close", table_cell), Paragraph("Reverse motor within 50ms upon obstacle force > 100N", table_cell), Paragraph("ASIL-A", table_cell)],
        [Paragraph("LightingMgrSWC", table_cell), Paragraph("Total loss of forward illumination at night", table_cell), Paragraph("Maintain low beam or activate backup parking lamp", table_cell), Paragraph("ASIL-B", table_cell)],
        [Paragraph("WiperWasherSWC", table_cell), Paragraph("Wiper stalls during heavy rain at speed", table_cell), Paragraph("Execute limp-home slow sweep mode", table_cell), Paragraph("ASIL-A", table_cell)],
        [Paragraph("ImmobilizerSWC", table_cell), Paragraph("Unauthorized engine start without valid key", table_cell), Paragraph("Prevent immobilizer token release", table_cell), Paragraph("QM", table_cell)],
    ]
    safety_table = Table(safety_data, colWidths=[90, 160, 190, 45])
    safety_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(safety_table)
    story.append(PageBreak())

    # ================= PAGE 5: SECTION 3: ARCHITECTURE & SECTION 4: SWCS =================
    story.append(Paragraph("3. AUTOSAR Architecture Overview & 4. Software Components", h1_style))
    story.append(Paragraph("3.1 Layered Structure & Virtual Function Bus (VFB)", h2_style))
    p3_arch = """
    The BCM architecture is partitioned into four primary AUTOSAR layers:
    Application Layer (10 Application SWCs), Runtime Environment (RTE), Basic Software (BSW), and Microcontroller Abstraction Layer (MCAL).
    All inter-SWC communication flows strictly through formal Ports and Interfaces across the RTE.
    """
    story.append(Paragraph(p3_arch, body_style))

    story.append(Paragraph("4.1 Software Component (SWC) Inventory", h2_style))
    story.append(Paragraph("The system defines 10 core Application Software Components:", body_style))

    swc_list = [
        ("DoorLockSWC", "Application", "ASIL-B", "20 ms", "Central door locking, child safety, auto-lock at 15 km/h, and emergency crash unlock override."),
        ("WindowCtrlSWC", "Application", "ASIL-A", "20 ms", "Power window motor positioning, express movement, and anti-pinch safety reverse algorithms."),
        ("LightingMgrSWC", "Application", "ASIL-B", "20 ms", "Headlamps, turn signals, hazard emergency flashers, and interior ambient lighting."),
        ("WiperWasherSWC", "Application", "ASIL-A", "50 ms", "Rain sensor processing, intermittent wiper pacing, and washer pump motor control."),
        ("ImmobilizerSWC", "Application", "QM", "100 ms", "Transponder key challenge-response cryptographic authentication with engine ECM."),
        ("SeatAdjustmentSWC", "Application", "QM", "100 ms", "Electric seat adjustment motors, Hall sensor feedback, and user memory presets."),
        ("CanComSWC", "Service Bridge", "ASIL-B", "10 ms", "CAN-FD frame serialization, signal filtering, E2E protection, and network management."),
        ("LinComSWC", "Service Bridge", "QM", "20 ms", "LIN master coordinator for rain sensor, mirror sub-nodes, and smart ambient LEDs."),
        ("DiagMgrSWC", "Diagnostics", "ASIL-B", "100 ms", "UDS ISO 14229 services, DTC fault logging, and freeze-frame snapshot capture."),
        ("PowerMgrSWC", "Mode Control", "ASIL-B", "20 ms", "ECU operational modes (Active, Standby, Sleep) and battery low-voltage load shedding.")
    ]

    swc_table_data = [[Paragraph("Component Name", table_hdr), Paragraph("Type", table_hdr), Paragraph("ASIL", table_hdr), Paragraph("Period", table_hdr), Paragraph("Functional Description", table_hdr)]]
    for s_name, s_type, s_asil, s_period, s_desc in swc_list:
        swc_table_data.append([
            Paragraph(f"<b>{s_name}</b>", table_cell),
            Paragraph(s_type, table_cell),
            Paragraph(s_asil, table_cell),
            Paragraph(s_period, table_cell),
            Paragraph(s_desc, table_cell)
        ])

    swc_table = Table(swc_table_data, colWidths=[95, 65, 45, 40, 240])
    swc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(swc_table)
    story.append(Spacer(1, 8))

    if is_v2:
        # Seeded Defect 4: Component referenced but never defined (SunroofCtrlSWC)
        story.append(Paragraph("4.2 Auxiliary System Dependencies", h2_style))
        aux_text = """
        <b>Note on Extended Cabin Modules:</b> In this revision, the rain-closure sequence delegates roof actuation
        to <b>SunroofCtrlSWC</b> (Refer to Section 7 for dependency specifications).
        """
        story.append(Paragraph(aux_text, callout_style))

    story.append(PageBreak())

    # ================= PAGE 6: SECTION 5: PORT & INTERFACE CATALOG =================
    story.append(Paragraph("5. Port and Interface Catalog", h1_style))
    story.append(Paragraph("5.1 Sender-Receiver (S/R) Interfaces", h2_style))
    story.append(Paragraph("The table below specifies all Sender-Receiver interfaces, data elements, data types, and units:", body_style))

    # Seeded Defect 3: Changed data type (VehicleSpeedKmh changed from Uint16 to Float32)
    speed_type = "Float32" if is_v2 else "Uint16"

    sr_if_data = [
        [Paragraph("Interface Name", table_hdr), Paragraph("Data Element", table_hdr), Paragraph("Data Type", table_hdr), Paragraph("Range / Enum", table_hdr), Paragraph("Unit", table_hdr)],
        [Paragraph("If_DoorLockStatus", table_cell), Paragraph("DoorLockState", table_cell), Paragraph("Uint8", table_cell), Paragraph("0:UNLOCKED, 1:LOCKED, 2:DEADLOCK", table_cell), Paragraph("Enum", table_cell)],
        [Paragraph("If_DoorLockStatus", table_cell), Paragraph("ChildLockActive", table_cell), Paragraph("Boolean", table_cell), Paragraph("0:False, 1:True", table_cell), Paragraph("Flag", table_cell)],
        [Paragraph("If_WindowState", table_cell), Paragraph("WindowPosition_FL", table_cell), Paragraph("Uint8", table_cell), Paragraph("0 to 100", table_cell), Paragraph("% Open", table_cell)],
        [Paragraph("If_WindowState", table_cell), Paragraph("AntiPinchTriggered", table_cell), Paragraph("Boolean", table_cell), Paragraph("0:False, 1:True", table_cell), Paragraph("Flag", table_cell)],
        [Paragraph("If_LightingCommand", table_cell), Paragraph("ExteriorLightMode", table_cell), Paragraph("Uint8", table_cell), Paragraph("0:OFF, 1:PARK, 2:LOW, 3:HIGH", table_cell), Paragraph("Enum", table_cell)],
        [Paragraph("If_LightingCommand", table_cell), Paragraph("HazardActive", table_cell), Paragraph("Boolean", table_cell), Paragraph("0:False, 1:True", table_cell), Paragraph("Flag", table_cell)],
        [Paragraph("If_VehicleSpeed", table_cell), Paragraph("VehicleSpeedKmh", table_cell), Paragraph(speed_type, table_cell), Paragraph("0 to 350", table_cell), Paragraph("km/h", table_cell)],
        [Paragraph("If_BatteryVoltage", table_cell), Paragraph("SupplyVoltage_mV", table_cell), Paragraph("Uint16", table_cell), Paragraph("0 to 32000", table_cell), Paragraph("mV", table_cell)],
        [Paragraph("If_BatteryVoltage", table_cell), Paragraph("LowVoltageWarning", table_cell), Paragraph("Boolean", table_cell), Paragraph("0:False, 1:True", table_cell), Paragraph("Flag", table_cell)],
        [Paragraph("If_WiperSpeedCmd", table_cell), Paragraph("WiperSpeedMode", table_cell), Paragraph("Uint8", table_cell), Paragraph("0:OFF, 1:INT1, 2:INT2, 3:LOW, 4:HIGH", table_cell), Paragraph("Enum", table_cell)],
        [Paragraph("If_RainIntensity", table_cell), Paragraph("RainSensorLevel", table_cell), Paragraph("Uint8", table_cell), Paragraph("0 to 255", table_cell), Paragraph("Raw Lux", table_cell)],
        [Paragraph("If_CrashStatus", table_cell), Paragraph("CrashDetected", table_cell), Paragraph("Boolean", table_cell), Paragraph("0:No Crash, 1:Crash Event", table_cell), Paragraph("Flag", table_cell)],
    ]

    if is_v2:
        # Seeded Defect 5: Interface with no consumer (If_TrailerHitchDetect)
        sr_if_data.append([Paragraph("If_TrailerHitchDetect", table_cell), Paragraph("TrailerAttached", table_cell), Paragraph("Boolean", table_cell), Paragraph("0:No Trailer, 1:Attached", table_cell), Paragraph("Flag", table_cell)])

    sr_table = Table(sr_if_data, colWidths=[110, 110, 65, 140, 60])
    sr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sr_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.2 Client-Server (C/S) Interfaces", h2_style))
    cs_if_data = [
        [Paragraph("Interface Name", table_hdr), Paragraph("Operation", table_hdr), Paragraph("Argument (Direction: Type)", table_hdr), Paragraph("Return Type", table_hdr)],
        [Paragraph("If_AuthSecurity", table_cell), Paragraph("AuthenticateKey", table_cell), Paragraph("IN seed: Uint32, OUT key: Uint32", table_cell), Paragraph("Std_ReturnType", table_cell)],
        [Paragraph("If_DiagDtcService", table_cell), Paragraph("SetDTC", table_cell), Paragraph("IN dtcId: Uint32, IN status: Uint8", table_cell), Paragraph("Std_ReturnType", table_cell)],
        [Paragraph("If_PowerModeControl", table_cell), Paragraph("RequestPowerState", table_cell), Paragraph("IN targetState: Uint8, OUT ack: Boolean", table_cell), Paragraph("Std_ReturnType", table_cell)],
    ]
    cs_table = Table(cs_if_data, colWidths=[120, 110, 175, 80])
    cs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(cs_table)
    story.append(PageBreak())

    # ================= PAGE 7: SECTION 5.3: COMPONENT DETAILED PROFILES =================
    story.append(Paragraph("5.3 Core Component Functional Profiles", h1_style))
    story.append(Paragraph("Profiles for DoorLockSWC, WindowCtrlSWC, LightingMgrSWC, and DiagMgrSWC:", body_style))

    profiles = [
        ("DoorLockSWC", "ASIL-B", "Central door locking, auto-lock above 15 km/h, and emergency crash unlock within 30ms.",
         "Runnable_DoorLock_20ms (Cyclic evaluation), Runnable_DoorLock_CrashEvent (Event interrupt)."),
        ("WindowCtrlSWC", "ASIL-A", "Express power window motion and anti-pinch safety reversal upon force > 100N.",
         "Runnable_WindowCtrl_20ms (Positioning loop), Runnable_PinchDetect_10ms (Current feedback)."),
        ("LightingMgrSWC", "ASIL-B", "Exterior headlamps, turn signal flashers, and emergency hazard flashers at 1.5 Hz.",
         "Runnable_Lighting_20ms (Arbitration), Runnable_HazardFlash_250ms (Cadence square-wave)."),
        ("DiagMgrSWC", "ASIL-B", "UDS ISO 14229 services, DTC fault logging, and non-volatile freeze-frame records.",
         "Runnable_Diag_100ms (Debounce counters), Runnable_UdsService_Handler (Diagnostic messages).")
    ]
    for cname, casil, cdesc, crun in profiles:
        story.append(Paragraph(f"<b>{cname} (Safety: {casil})</b>", h2_style))
        story.append(Paragraph(f"<b>Functional Behavior:</b> {cdesc}", body_style))
        story.append(Paragraph(f"<b>Runnable Entities:</b> {crun}", body_style))
        story.append(Spacer(1, 4))
    story.append(PageBreak())

    # ================= PAGE 8: SECTION 6: SIGNAL LIST & BUS ALLOCATION =================
    story.append(Paragraph("6. Signal List, Data Mapping and Bus Allocation", h1_style))
    story.append(Paragraph("6.1 CAN-FD & LIN Signal Table", h2_style))
    story.append(Paragraph("The following table details every network signal mapped to CAN-FD (Channel 1) or LIN (Channel 0):", body_style))

    # Seeded Defect 1: 2 Renamed Signals
    # Sig_DoorState_FrontLeft -> Sig_DoorState_FL_Status
    # Sig_HeadlampStatus -> Sig_ExteriorHeadlamp_State
    sig_door_front = "Sig_DoorState_FL_Status" if is_v2 else "Sig_DoorState_FrontLeft"
    sig_headlamp = "Sig_ExteriorHeadlamp_State" if is_v2 else "Sig_HeadlampStatus"

    signals_data = [
        [Paragraph("Signal Name", table_hdr), Paragraph("Type", table_hdr), Paragraph("Cycle", table_hdr), Paragraph("Bus", table_hdr), Paragraph("Source SWC", table_hdr), Paragraph("Destination SWC", table_hdr)],
        [Paragraph(sig_door_front, table_cell), Paragraph("Uint8", table_cell), Paragraph("20 ms", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("CanComSWC", table_cell), Paragraph("DoorLockSWC", table_cell)],
        [Paragraph("Sig_AutoLockSpeedThreshold", table_cell), Paragraph("Uint16", table_cell), Paragraph("100 ms", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("CanComSWC", table_cell), Paragraph("DoorLockSWC", table_cell)],
        [Paragraph("Sig_CrashNotification", table_cell), Paragraph("Boolean", table_cell), Paragraph("10 ms", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("CanComSWC", table_cell), Paragraph("DoorLockSWC", table_cell)],
        [Paragraph(sig_headlamp, table_cell), Paragraph("Uint8", table_cell), Paragraph("50 ms", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("LightingMgrSWC", table_cell), Paragraph("CanComSWC", table_cell)],
        [Paragraph("Sig_RainSensorVal", table_cell), Paragraph("Uint8", table_cell), Paragraph("100 ms", table_cell), Paragraph("LIN", table_cell), Paragraph("LinComSWC", table_cell), Paragraph("WiperWasherSWC", table_cell)],
        [Paragraph("Sig_WindowObstacleDetected", table_cell), Paragraph("Boolean", table_cell), Paragraph("20 ms", table_cell), Paragraph("Internal", table_cell), Paragraph("WindowCtrlSWC", table_cell), Paragraph("DiagMgrSWC", table_cell)],
        [Paragraph("Sig_BatterySupplyMV", table_cell), Paragraph("Uint16", table_cell), Paragraph("1000 ms", table_cell), Paragraph("Internal", table_cell), Paragraph("PowerMgrSWC", table_cell), Paragraph("DiagMgrSWC", table_cell)],
        [Paragraph("Sig_IgnitionSwitchPos", table_cell), Paragraph("Uint8", table_cell), Paragraph("20 ms", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("CanComSWC", table_cell), Paragraph("PowerMgrSWC", table_cell)],
        [Paragraph("Sig_TurnSignalRequest", table_cell), Paragraph("Uint8", table_cell), Paragraph("50 ms", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("LightingMgrSWC", table_cell), Paragraph("CanComSWC", table_cell)],
        [Paragraph("Sig_SeatMemoryPresetIndex", table_cell), Paragraph("Uint8", table_cell), Paragraph("200 ms", table_cell), Paragraph("CAN-FD", table_cell), Paragraph("SeatAdjustmentSWC", table_cell), Paragraph("CanComSWC", table_cell)],
        [Paragraph("Sig_WiperParkPosition", table_cell), Paragraph("Boolean", table_cell), Paragraph("50 ms", table_cell), Paragraph("Internal", table_cell), Paragraph("WiperWasherSWC", table_cell), Paragraph("CanComSWC", table_cell)],
        [Paragraph("Sig_AmbientBrightnessLux", table_cell), Paragraph("Uint16", table_cell), Paragraph("500 ms", table_cell), Paragraph("LIN", table_cell), Paragraph("LinComSWC", table_cell), Paragraph("LightingMgrSWC", table_cell)],
    ]
    sig_table = Table(signals_data, colWidths=[130, 45, 45, 55, 95, 115])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sig_table)
    story.append(PageBreak())

    # ================= PAGE 9: SECTION 7: COMPONENT DEPENDENCIES & PORTS =================
    story.append(Paragraph("7. Component Dependencies and Port Connections", h1_style))
    story.append(Paragraph("7.1 Component Port Bindings", h2_style))
    story.append(Paragraph("The following table details Provided Ports (PPorts) and Required Ports (RPorts) across key SWCs:", body_style))

    # Seeded Defect 2: 1 Removed port (p_DoorLockStatus removed from DoorLockSWC)
    port_bindings = [
        ("DoorLockSWC",
         "[REMOVED IN v2]" if is_v2 else "p_DoorLockStatus (If_DoorLockStatus)",
         "r_VehicleSpeed (If_VehicleSpeed), r_CrashStatus (If_CrashStatus), r_PowerState (If_PowerModeControl)"),
        ("WindowCtrlSWC",
         "p_WindowState (If_WindowState)",
         "r_VehicleSpeed (If_VehicleSpeed), r_PowerState (If_PowerModeControl)"),
        ("LightingMgrSWC",
         "p_LightingCommand (If_LightingCommand)" + (", p_TrailerHitch (If_TrailerHitchDetect)" if is_v2 else ""),
         "r_PowerState (If_PowerModeControl), r_CrashStatus (If_CrashStatus)"),
        ("WiperWasherSWC",
         "p_WiperSpeedCmd (If_WiperSpeedCmd)",
         "r_VehicleSpeed (If_VehicleSpeed), r_RainIntensity (If_RainIntensity)"),
        ("CanComSWC",
         "p_VehicleSpeed (If_VehicleSpeed), p_CrashStatus (If_CrashStatus)",
         "r_DoorLockStatus (If_DoorLockStatus), r_LightingCommand (If_LightingCommand)"),
        ("PowerMgrSWC",
         "p_PowerState (If_PowerModeControl), p_BatteryVoltage (If_BatteryVoltage)",
         "r_IgnitionSwitch (If_VehicleSpeed)"),
        ("DiagMgrSWC",
         "p_DiagDtcService (If_DiagDtcService)",
         "r_BatteryVoltage (If_BatteryVoltage)"),
        ("ImmobilizerSWC",
         "p_AuthSecurity (If_AuthSecurity)",
         "r_PowerState (If_PowerModeControl)")
    ]

    port_table_data = [[Paragraph("Software Component", table_hdr), Paragraph("Provided Ports (PPort)", table_hdr), Paragraph("Required Ports (RPort)", table_hdr)]]
    for swc, pports, rports in port_bindings:
        port_table_data.append([
            Paragraph(f"<b>{swc}</b>", table_cell),
            Paragraph(pports, table_cell),
            Paragraph(rports, table_cell)
        ])

    port_tbl = Table(port_table_data, colWidths=[110, 165, 210])
    port_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(port_tbl)
    story.append(Spacer(1, 15))

    story.append(Paragraph("7.2 Coupling Constraints & Power Shedding Rules", h2_style))
    p7_rules = """
    1. <b>Safety Priority:</b> <code>DoorLockSWC</code> and <code>LightingMgrSWC</code> must prioritize signals
    originating from <code>p_CrashStatus</code> above all convenience and user switch requests.
    <br/>2. <b>Coupling Rules:</b> Inter-SWC communication flows exclusively through intermediate RTE buffers.
    <br/>3. <b>Power Shedding:</b> If <code>SupplyVoltage_mV</code> drops below 10,500 mV, <code>PowerMgrSWC</code>
    sheds seat heaters, power windows, and ambient lighting sequentially.
    """
    story.append(Paragraph(p7_rules, body_style))
    story.append(PageBreak())

    # ================= PAGE 10: SECTION 8: HARDWARE INTERFACE PINOUT =================
    story.append(Paragraph("8. Hardware Interface & Connector Pinout", h1_style))
    story.append(Paragraph("8.1 Physical Connector Pin Allocations", h2_style))
    story.append(Paragraph("The table below details physical connector allocations for the BCM ECU:", body_style))

    pinout_data = [
        [Paragraph("Pin ID", table_hdr), Paragraph("Connector", table_hdr), Paragraph("Signal Name", table_hdr), Paragraph("Electrical Spec", table_hdr), Paragraph("Fail-Safe Default", table_hdr), Paragraph("ASIL", table_hdr)],
        [Paragraph("PIN_01", table_cell), Paragraph("CN-A", table_cell), Paragraph(sig_door_front, table_cell), Paragraph("0-12V Digital Input", table_cell), Paragraph("HIGH_IMPEDANCE", table_cell), Paragraph("ASIL-B", table_cell)],
        [Paragraph("PIN_02", table_cell), Paragraph("CN-A", table_cell), Paragraph("Sig_DoorState_FrontRight", table_cell), Paragraph("0-12V Digital Input", table_cell), Paragraph("HIGH_IMPEDANCE", table_cell), Paragraph("ASIL-B", table_cell)],
        [Paragraph("PIN_03", table_cell), Paragraph("CN-A", table_cell), Paragraph("Sig_EmergencyCrashPulse", table_cell), Paragraph("0-5V TTL Interrupt", table_cell), Paragraph("PULL_HIGH (TRIP)", table_cell), Paragraph("ASIL-D", table_cell)],
        [Paragraph("PIN_04", table_cell), Paragraph("CN-B", table_cell), Paragraph("Sig_CanHigh_HS_Ch1", table_cell), Paragraph("CAN-FD ISO 11898-2", table_cell), Paragraph("RECESSIVE", table_cell), Paragraph("ASIL-C", table_cell)],
        [Paragraph("PIN_05", table_cell), Paragraph("CN-B", table_cell), Paragraph("Sig_CanLow_HS_Ch1", table_cell), Paragraph("CAN-FD ISO 11898-2", table_cell), Paragraph("RECESSIVE", table_cell), Paragraph("ASIL-C", table_cell)],
        [Paragraph("PIN_06", table_cell), Paragraph("CN-C", table_cell), Paragraph("Sig_LinBusMaster_Ch0", table_cell), Paragraph("LIN 2.2A Single Wire", table_cell), Paragraph("RECESSIVE", table_cell), Paragraph("QM", table_cell)],
        [Paragraph("PIN_07", table_cell), Paragraph("CN-C", table_cell), Paragraph("Sig_RainSensorVal_Pin", table_cell), Paragraph("PWM 100Hz 5V", table_cell), Paragraph("DUTY_50_DEFAULT", table_cell), Paragraph("QM", table_cell)],
        [Paragraph("PIN_08", table_cell), Paragraph("CN-D", table_cell), Paragraph("Sig_HeadlampRelayHigh", table_cell), Paragraph("12V 25A Driver", table_cell), Paragraph("FORCE_OFF", table_cell), Paragraph("ASIL-B", table_cell)],
        [Paragraph("PIN_09", table_cell), Paragraph("CN-D", table_cell), Paragraph("Sig_HazardFlasherDirect", table_cell), Paragraph("12V 15A Pulsed", table_cell), Paragraph("FORCE_FLASHING", table_cell), Paragraph("ASIL-C", table_cell)],
        [Paragraph("PIN_10", table_cell), Paragraph("CN-E", table_cell), Paragraph("Sig_WiperParkSwitch", table_cell), Paragraph("Active-Low Ground", table_cell), Paragraph("WIPER_HOME", table_cell), Paragraph("ASIL-A", table_cell)],
        [Paragraph("PIN_11", table_cell), Paragraph("CN-E", table_cell), Paragraph("Sig_WindowPinchSense", table_cell), Paragraph("Current 0-20mA", table_cell), Paragraph("STOP_REVERSE", table_cell), Paragraph("ASIL-B", table_cell)],
        [Paragraph("PIN_12", table_cell), Paragraph("CN-F", table_cell), Paragraph("Sig_VBat_SupplyMonitor", table_cell), Paragraph("Analog ADC 0-32V", table_cell), Paragraph("NOMINAL_12V", table_cell), Paragraph("ASIL-B", table_cell)],
    ]
    pin_table = Table(pinout_data, colWidths=[45, 55, 125, 110, 100, 50])
    pin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(pin_table)
    story.append(PageBreak())

    # ================= PAGE 11: SECTION 9: FUNCTIONAL FLOW SEQUENCES =================
    story.append(Paragraph("9. Functional Flow Sequences", h1_style))
    story.append(Paragraph("9.1 Flow 1: Automatic Speed-Dependent Door Locking (Auto-Lock)", h2_style))
    flow1_text = """
    <b>Precondition:</b> Vehicle engine is running, passenger doors closed, initial speed 0 km/h.
    <br/><br/>
    <b>Execution Steps:</b>
    <br/>1. Wheel speed sensors transmit periodic pulses to ABS/ESP ECU.
    <br/>2. ESP ECU broadcasts velocity on CAN-FD Channel 1.
    <br/>3. <code>CanComSWC</code> unpacks CAN frame and writes <code>VehicleSpeedKmh</code> to RTE port <code>p_VehicleSpeed</code>.
    <br/>4. <code>DoorLockSWC</code> evaluates <code>r_VehicleSpeed</code> at 20ms invocation period.
    <br/>5. When <code>VehicleSpeedKmh</code> exceeds 15 km/h:
    <br/>&nbsp;&nbsp;&nbsp;&nbsp;a. <code>DoorLockSWC</code> asserts output latch driver signals for all 4 doors simultaneously.
    <br/>&nbsp;&nbsp;&nbsp;&nbsp;b. Hardware solenoids energize for 120ms driving latches to LOCKED position.
    <br/>&nbsp;&nbsp;&nbsp;&nbsp;c. <code>DoorLockSWC</code> updates <code>DoorLockState = 1 (LOCKED)</code> on port <code>p_DoorLockStatus</code>.
    <br/>6. Cluster display receives lock status confirmation and activates icon.
    """
    story.append(Paragraph(flow1_text, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("9.2 Flow 2: Crash Hazard Unlock and Lighting Response", h2_style))
    flow2_text = """
    <b>Precondition:</b> Vehicle is in motion or stationary; door latches are in LOCKED position.
    <br/><br/>
    <b>Execution Steps:</b>
    <br/>1. Airbag Restraint Control Module (RCM) detects crash deceleration exceeding 5g.
    <br/>2. RCM asserts discrete hardwired interrupt line PIN_03 and broadcasts Crash CAN-FD frame.
    <br/>3. <code>CanComSWC</code> asserts <code>p_CrashStatus.CrashDetected = TRUE</code> within < 5ms.
    <br/>4. <code>DoorLockSWC</code> intercepts crash event via <code>r_CrashStatus</code>:
    <br/>&nbsp;&nbsp;&nbsp;&nbsp;a. Overrides manual lock switch commands and child lock inhibitions.
    <br/>&nbsp;&nbsp;&nbsp;&nbsp;b. Pulses unlock solenoid drivers for 250ms to force latches into UNLOCKED state.
    <br/>5. <code>LightingMgrSWC</code> receives emergency trigger:
    <br/>&nbsp;&nbsp;&nbsp;&nbsp;a. Immediately engages hazard flasher relays at continuous 1.5 Hz cadence.
    <br/>&nbsp;&nbsp;&nbsp;&nbsp;b. Activates interior ambient courtesy lamps at 100% brightness.
    <br/>6. <code>DiagMgrSWC</code> registers crash freeze-frame record and locks DTC B10A2 into EEPROM.
    """
    story.append(Paragraph(flow2_text, body_style))
    story.append(PageBreak())

    # ================= PAGE 12: SECTION 10: DIAGNOSTICS & DTC MATRIX =================
    story.append(Paragraph("10. Diagnostic Specifications & DTC Matrix", h1_style))
    story.append(Paragraph("10.1 UDS ISO 14229 Service Support", h2_style))
    p10_uds = """
    The BCM diagnostic stack implements Unified Diagnostic Services (UDS) over ISO-TP:
    <br/>• <b>Service 0x10:</b> Diagnostic Session Control (Default, Programming, Extended Sessions).
    <br/>• <b>Service 0x14:</b> Clear Diagnostic Information (Group 0xFFFFFF).
    <br/>• <b>Service 0x19:</b> Read DTC Information (sub-functions 0x02 reportByStatusMask, 0x06 reportSnapshotRecord).
    <br/>• <b>Service 0x22:</b> Read Data by Identifier (DID read for battery voltage, software version).
    <br/>• <b>Service 0x27:</b> Security Access (Seed-Key authentication).
    <br/>• <b>Service 0x2E:</b> Write Data by Identifier (VIN write, end-of-line calibration).
    """
    story.append(Paragraph(p10_uds, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("10.2 Diagnostic Trouble Code Matrix", h2_style))
    dtc_data = [
        [Paragraph("DTC ID", table_hdr), Paragraph("Fault Code Title", table_hdr), Paragraph("Fault Trigger Condition", table_hdr), Paragraph("Recovery Criteria", table_hdr), Paragraph("Severity", table_hdr)],
        [Paragraph("B10A2", table_cell), Paragraph("Crash Event Recorded", table_cell), Paragraph("Continuous LOW on PIN_03 or crash CAN pulse", table_cell), Paragraph("Non-erasable without Security Level 27", table_cell), Paragraph("Critical", table_cell)],
        [Paragraph("B1001", table_cell), Paragraph("Front Left Door Latch Jammed", table_cell), Paragraph("Solenoid energizes for > 500ms without state change", table_cell), Paragraph("Cycle manual door handle 3 times", table_cell), Paragraph("Medium", table_cell)],
        [Paragraph("B1020", table_cell), Paragraph("Anti-Pinch Sensor Open Circuit", table_cell), Paragraph("Analog sensor resistance > 100 kOhm", table_cell), Paragraph("Resistance returns to 5 - 20 kOhm for 2 sec", table_cell), Paragraph("High", table_cell)],
        [Paragraph("B1035", table_cell), Paragraph("Headlamp Relay High-Side Short", table_cell), Paragraph("PROFET detects overcurrent (> 35A) during activation", table_cell), Paragraph("Auto-retry after 30 sec cooling period", table_cell), Paragraph("High", table_cell)],
        [Paragraph("B1044", table_cell), Paragraph("Rain Sensor Bus Timeout", table_cell), Paragraph("No LIN response frame from sensor for > 500ms", table_cell), Paragraph("Successful LIN header reply received", table_cell), Paragraph("Low", table_cell)],
        [Paragraph("U0100", table_cell), Paragraph("Lost Comms with Engine ECM", table_cell), Paragraph("CAN message 0x100 missing for > 200ms", table_cell), Paragraph("10 consecutive valid CAN frames received", table_cell), Paragraph("High", table_cell)],
        [Paragraph("P0562", table_cell), Paragraph("System Voltage Low (LVS)", table_cell), Paragraph("Battery voltage drops below 9.0V for > 5 seconds", table_cell), Paragraph("Battery voltage rises above 10.5V for 3 seconds", table_cell), Paragraph("Medium", table_cell)],
    ]
    dtc_table = Table(dtc_data, colWidths=[55, 140, 150, 110, 45])
    dtc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(dtc_table)
    story.append(PageBreak())

    # ================= PAGE 13: SECTION 11: VERIFICATION & TEST TRACEABILITY =================
    story.append(Paragraph("11. Verification Matrix & Traceability", h1_style))
    story.append(Paragraph("11.1 Requirement to Test Case Mapping", h2_style))
    test_data = [
        [Paragraph("Req ID", table_hdr), Paragraph("Requirement Description", table_hdr), Paragraph("Allocated SWC", table_hdr), Paragraph("Target Test Method", table_hdr)],
        [Paragraph("REQ-BCM-001", table_cell), Paragraph("Doors must lock automatically when vehicle speed exceeds 15 km/h", table_cell), Paragraph("DoorLockSWC", table_cell), Paragraph("Hardware-in-the-Loop (HIL) CAN injection", table_cell)],
        [Paragraph("REQ-BCM-002", table_cell), Paragraph("All latches must unlock within 30ms of collision pulse reception", table_cell), Paragraph("DoorLockSWC", table_cell), Paragraph("Digital oscilloscope hardware timing verify", table_cell)],
        [Paragraph("REQ-BCM-003", table_cell), Paragraph("Hazard lights must oscillate at 1.5 Hz during crash condition", table_cell), Paragraph("LightingMgrSWC", table_cell), Paragraph("CAN and relay pulse frequency counter", table_cell)],
        [Paragraph("REQ-BCM-004", table_cell), Paragraph("Window express upward movement must reverse upon >100N pinch resistance", table_cell), Paragraph("WindowCtrlSWC", table_cell), Paragraph("Mechanical pinch rig calibrated load cell", table_cell)],
        [Paragraph("REQ-BCM-005", table_cell), Paragraph("System must enter Low Voltage Sleep if VBat remains < 9V for 5s", table_cell), Paragraph("PowerMgrSWC", table_cell), Paragraph("Programmable DC bench power supply drop test", table_cell)],
    ]
    test_table = Table(test_data, colWidths=[75, 195, 100, 130])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(test_table)
    story.append(PageBreak())

    # ================= PAGE 14: SECTION 12: GLOSSARY =================
    story.append(Paragraph("12. Glossary and Terminology Definitions", h1_style))
    story.append(Paragraph("Section 12.1: Standard Architectural Glossary", h2_style))
    glossary_items = [
        ("SWC", "Software Component: Self-contained functional unit encapsulated according to the AUTOSAR component model."),
        ("RTE", "Runtime Environment: Virtual Function Bus (VFB) middleware linking SWC ports to BSW or each other."),
        ("BSW", "Basic Software: Standardized software layers including Services, ECUM, Com, and MCAL drivers."),
        ("S/R Interface", "Sender-Receiver Interface: Asynchronous data broadcast communication pattern between ports."),
        ("C/S Interface", "Client-Server Interface: Synchronous or asynchronous operation invocation between ports."),
        ("DTC", "Diagnostic Trouble Code: 3-byte identifier specifying fault classification and symptom."),
        ("ASIL", "Automotive Safety Integrity Level: ISO 26262 risk classification (QM, ASIL-A through ASIL-D)."),
        ("UDS", "Unified Diagnostic Services: ISO 14229 protocol standard for automotive diagnostic exchange.")
    ]
    gloss_data = [[Paragraph("Term", table_hdr), Paragraph("Definition", table_hdr)]]
    for t, d in glossary_items:
        gloss_data.append([Paragraph(f"<b>{t}</b>", table_cell), Paragraph(d, table_cell)])
    gloss_table = Table(gloss_data, colWidths=[90, 395])
    gloss_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(gloss_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Section 12.2: Governance Sign-off Note", h2_style))
    story.append(Paragraph("This concludes the formal High-Level Design specification for the Body Control Module. Revisions must follow formal ECN review procedures.", body_style))

    canvas_cls = NumberedCanvas
    canvas_cls.is_v2 = is_v2
    doc.build(story, canvasmaker=canvas_cls)
    return output_path


def generate_defect_ground_truth(filepath: Path):
    """Generates seeded_defects_ground_truth.json containing the 5 seeded changes for 90-minute scope."""
    ground_truth = {
        "metadata": {
            "title": "Ground Truth Seeded Architectural Defects (HLD_BodyControl_v2.pdf vs v1.pdf)",
            "baseline_document": "HLD_BodyControl_v1.pdf",
            "revised_document": "HLD_BodyControl_v2.pdf",
            "total_seeded_defects": 6,
            "verification_purpose": "Automated RAG and architectural comparison rule validation"
        },
        "defects": [
            {
                "defect_id": "DEF-SIG-01",
                "category": "renamed_signal",
                "v1_identifier": "Sig_DoorState_FrontLeft",
                "v2_identifier": "Sig_DoorState_FL_Status",
                "section": "Section 6.1 (Signal List)",
                "page": 8,
                "severity": "High",
                "description": "Signal renamed without corresponding CAN interface alias definition."
            },
            {
                "defect_id": "DEF-SIG-02",
                "category": "renamed_signal",
                "v1_identifier": "Sig_HeadlampStatus",
                "v2_identifier": "Sig_ExteriorHeadlamp_State",
                "section": "Section 6.1 (Signal List)",
                "page": 8,
                "severity": "Medium",
                "description": "Signal renamed, breaking LightingMgrSWC downstream telemetry link."
            },
            {
                "defect_id": "DEF-PORT-01",
                "category": "removed_port",
                "component": "DoorLockSWC",
                "port_name": "p_DoorLockStatus",
                "port_type": "PPort",
                "interface": "If_DoorLockStatus",
                "section": "Section 7.1 (Component Port Bindings)",
                "page": 9,
                "severity": "Critical",
                "description": "PPort p_DoorLockStatus removed from DoorLockSWC, leaving CanComSWC r_DoorLockStatus unsupplied."
            },
            {
                "defect_id": "DEF-TYPE-01",
                "category": "changed_data_type",
                "interface": "If_VehicleSpeed",
                "element": "VehicleSpeedKmh",
                "v1_type": "Uint16",
                "v2_type": "Float32",
                "section": "Section 5.1 (S/R Interfaces)",
                "page": 6,
                "severity": "High",
                "description": "Vehicle speed data type changed from integer (Uint16) to floating-point (Float32)."
            },
            {
                "defect_id": "DEF-UNDEF-01",
                "category": "undefined_component_reference",
                "component_name": "SunroofCtrlSWC",
                "section": "Section 4.2 (Auxiliary System Dependencies)",
                "page": 5,
                "severity": "High",
                "description": "Component SunroofCtrlSWC referenced for rain auto-closure, but missing from SWC inventory."
            },
            {
                "defect_id": "DEF-ORPHAN-01",
                "category": "orphaned_interface",
                "interface_name": "If_TrailerHitchDetect",
                "provider": "LightingMgrSWC",
                "consumer": "None (Unconnected)",
                "section": "Section 5.1 & Section 7.1",
                "page": 6,
                "severity": "Medium",
                "description": "Trailer detection interface provided by LightingMgrSWC but never consumed by any SWC or BSW."
            }
        ]
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)
    return filepath


def generate_data_sources_note(filepath: Path):
    content = """# Data Sources and Synthetic Generation Declaration

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
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    return filepath


def main():
    print("=" * 60)
    print("STEP 2: Generating Synthetic AUTOSAR HLD Documents (14 Pages)")
    print("=" * 60)

    v1_pdf = INPUT_DATA_DIR / "HLD_BodyControl_v1.pdf"
    print(f"[1/4] Building Baseline Document: {v1_pdf.name}...")
    build_pdf_document(v1_pdf, version="v1")
    print(f"      -> Successfully created {v1_pdf.name} ({v1_pdf.stat().st_size / 1024:.1f} KB)")

    v2_pdf = INPUT_DATA_DIR / "HLD_BodyControl_v2.pdf"
    print(f"[2/4] Building Revised Document: {v2_pdf.name}...")
    build_pdf_document(v2_pdf, version="v2")
    print(f"      -> Successfully created {v2_pdf.name} ({v2_pdf.stat().st_size / 1024:.1f} KB)")

    gt_json = INPUT_DATA_DIR / "seeded_defects_ground_truth.json"
    print(f"[3/4] Writing Ground Truth Defect Catalog: {gt_json.name}...")
    generate_defect_ground_truth(gt_json)
    print(f"      -> Successfully created {gt_json.name}")

    ds_md = INPUT_DATA_DIR / "DATA_SOURCES.md"
    print(f"[4/4] Generating Provenance & License Declaration: {ds_md.name}...")
    generate_data_sources_note(ds_md)
    print(f"      -> Successfully created {ds_md.name}")

    print("=" * 60)
    print("[SUCCESS] Step 2 Synthetic Data generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
