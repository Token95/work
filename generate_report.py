import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# =====================================================================
# BRAND COLORS
# =====================================================================

SMARTCON_GREEN  = colors.HexColor("#4A7C2F")
SMARTCON_YELLOW = colors.HexColor("#F5C400")
SMARTCON_DARK   = colors.HexColor("#1A1A1A")
SMARTCON_GRAY   = colors.HexColor("#666666")
SMARTCON_LIGHT  = colors.HexColor("#F5F5F5")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "smartcon_logo.png")

# =====================================================================
# STYLES
# =====================================================================

def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=24,
            textColor=SMARTCON_GREEN,
            spaceAfter=8,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=SMARTCON_DARK,
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=SMARTCON_GREEN,
            spaceBefore=14,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9,
            textColor=SMARTCON_DARK,
            spaceAfter=3,
            leading=14,
        ),
        "step": ParagraphStyle(
            "step",
            fontName="Helvetica",
            fontSize=9,
            textColor=SMARTCON_DARK,
            spaceAfter=3,
            leftIndent=12,
            leading=14,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=SMARTCON_GRAY,
            alignment=TA_CENTER,
        ),
        "label": ParagraphStyle(
            "label",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=SMARTCON_DARK,
        ),
        "value": ParagraphStyle(
            "value",
            fontName="Helvetica",
            fontSize=9,
            textColor=SMARTCON_DARK,
        ),
    }
    return styles

# =====================================================================
# HEADER / FOOTER
# =====================================================================

def on_page(canvas, doc):
    canvas.saveState()
    width, height = letter

    # Top rule
    canvas.setStrokeColor(SMARTCON_GREEN)
    canvas.setLineWidth(2)
    canvas.line(0.5 * inch, height - 0.55 * inch,
                width - 0.5 * inch, height - 0.55 * inch)

    # Footer text
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SMARTCON_GRAY)
    canvas.drawCentredString(
        width / 2,
        0.35 * inch,
       f"SMARTCON SOLUTIONS  |  Field Operations Manual  |  "
        f"Generated {datetime.date.today().strftime('%B %d, %Y')}  |  Page {doc.page}"
    )

    # Footer rule
    canvas.setStrokeColor(SMARTCON_YELLOW)
    canvas.setLineWidth(1.5)
    canvas.line(0.5 * inch, 0.5 * inch,
                width - 0.5 * inch, 0.5 * inch)

    canvas.restoreState()

# =====================================================================
# DATA TABLE BUILDER
# =====================================================================

def build_data_table(extracted_data, styles):
    rows = [
        ["Target Property",     extracted_data.get("Hotel", "N/A")],
        ["City / State",        extracted_data.get("City", "N/A")],
        ["Revision",            extracted_data.get("Revision", "N/A")],
        ["Date",                extracted_data.get("Date", "N/A")],
        ["Drafter",             extracted_data.get("Drafter", "N/A")],
        ["Reviewer",            extracted_data.get("Reviewer", "N/A")],
        ["Vendor / Platform",   extracted_data.get("Vendor", "N/A")],
        ["Thermostat Model",    extracted_data.get("Thermostat_Model", "N/A")],
        ["Network Type",        extracted_data.get("Network_Type", "N/A")],
        ["HVAC Description",    extracted_data.get("HVAC_Description", "N/A")],
        ["HVAC Model",          extracted_data.get("HVAC_Model", "N/A")],
        ["Voltage",             extracted_data.get("Voltage", "N/A")],
        ["Equipment Code",      extracted_data.get("Equipment_Code", "N/A")],
        ["Fan Speed",           extracted_data.get("Fan_Speed", "N/A")],
        ["Occupied Cool",       extracted_data.get("Occupied_Cool", "N/A")],
        ["Occupied Heat",       extracted_data.get("Occupied_Heat", "N/A")],
        ["Unoccupied Cool",     extracted_data.get("Unoccupied_Cool", "N/A")],
        ["Unoccupied Heat",     extracted_data.get("Unoccupied_Heat", "N/A")],
        ["Grace Period",        extracted_data.get("Grace_Period", "N/A")],
        ["PMS",                 extracted_data.get("PMS", "N/A")],
        ["PAN ID",              extracted_data.get("PAN_ID", "N/A")],
        ["RF Channel",          extracted_data.get("RF_Channel", "N/A")],
        ["Door Locks",          extracted_data.get("Door_Locks", "N/A")],
        ["Occupancy Sensors",   extracted_data.get("Occupancy_Sensors", "N/A")],
        ["Door Contact",        extracted_data.get("Door_Contact", "N/A")],
    ]

    table_data = [
        [Paragraph(label, styles["label"]),
         Paragraph(str(value), styles["value"])]
        for label, value in rows
    ]

    table = Table(table_data, colWidths=[2.2 * inch, 4.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), SMARTCON_LIGHT),
        ("TEXTCOLOR",   (0, 0), (-1, -1), SMARTCON_DARK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.white, SMARTCON_LIGHT]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    return table

# =====================================================================
# BINDING STEPS BUILDER
# =====================================================================

def build_binding_steps(profile, styles):
    elements = []
    steps = profile.get("binding_steps", {})

    if isinstance(steps, dict):
        for section, step_list in steps.items():
            elements.append(Paragraph(
                section.replace("_", " ").upper(),
                styles["section_header"]
            ))
            elements.append(HRFlowable(
                width="100%", thickness=0.5,
                color=SMARTCON_YELLOW, spaceAfter=4
            ))
            if isinstance(step_list, list):
                for i, step in enumerate(step_list, 1):
                    elements.append(Paragraph(
                        f"{i}.  {step}", styles["step"]
                    ))
            elements.append(Spacer(1, 8))

    elif isinstance(steps, list):
        for i, step in enumerate(steps, 1):
            elements.append(Paragraph(f"{i}.  {step}", styles["step"]))

    return elements

# =====================================================================
# MAIN REPORT GENERATOR
# =====================================================================

def generate_report(extracted_data, profile, rooms=None, floor_summary=None, output_path="Smartcon_Field_Ops_Manual.pdf"):
    styles = build_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.8 * inch,
    )

    elements = []

    # --- COVER: LOGO ---
    if os.path.exists(LOGO_PATH):
        print(f"[+] Logo loaded: {LOGO_PATH}")
        logo = Image(LOGO_PATH, width=3.2 * inch, height=0.85 * inch)
        logo.hAlign = "CENTER"
        elements.append(logo)
    else:
        print(f"[-] Logo not found at: {LOGO_PATH}")
        elements.append(Paragraph("SMARTCON SOLUTIONS", styles["title"]))

    elements.append(Spacer(1, 20))

    # --- COVER: TITLE ---
    elements.append(Paragraph("Field Operations Manual", ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=SMARTCON_GREEN,
        spaceAfter=10,
        alignment=TA_CENTER,
    )))

    elements.append(Spacer(1, 10))

    # --- COVER: HOTEL NAME ---
    hotel = extracted_data.get("Hotel", "")
    city  = extracted_data.get("City", "")

    if hotel and hotel != "Not found":
        elements.append(Paragraph(hotel, ParagraphStyle(
            "cover_hotel",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=SMARTCON_DARK,
            spaceAfter=6,
            alignment=TA_CENTER,
        )))

    # --- COVER: CITY ---
    if city and city != "Not found" and len(city) < 35:
        elements.append(Paragraph(city, ParagraphStyle(
            "cover_city",
            fontName="Helvetica",
            fontSize=11,
            textColor=SMARTCON_GRAY,
            spaceAfter=4,
            alignment=TA_CENTER,
        )))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(
        width="100%", thickness=2,
        color=SMARTCON_GREEN, spaceAfter=10
    ))

    # --- META LINE ---
    meta = (
        f"Generated: {datetime.date.today().strftime('%B %d, %Y')}   |   "
        f"Prepared by: Devon Brown   |   "
        f"Revision: {extracted_data.get('Revision', 'N/A')}   |   "
        f"Service ID: SRV-{datetime.date.today().strftime('%Y%m%d')}-AUTO"
    )
    elements.append(Paragraph(meta, styles["footer"]))
    elements.append(Spacer(1, 20))

    # --- SECTION 1: PROJECT DATA TABLE ---
    elements.append(Paragraph("1.  Site Submittal Extraction", styles["section_header"]))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=SMARTCON_YELLOW, spaceAfter=6
    ))
    elements.append(build_data_table(extracted_data, styles))
    elements.append(Spacer(1, 16))

    # --- SECTION 2: COMMISSIONING STEPS ---
    if profile:
        elements.append(PageBreak())
        elements.append(Paragraph(
            "2.  Commissioning & Pairing Procedure", styles["section_header"]
        ))
        elements.append(Paragraph(
            f"Platform: {profile.get('platform', 'N/A')}   |   "
            f"Tool: {profile.get('software_tool', 'N/A')}",
            styles["body"]
        ))
        elements.append(Spacer(1, 8))
        elements.extend(build_binding_steps(profile, styles))

   # --- SECTION 3: ROOM MATRIX ---
    if rooms:
        elements.append(PageBreak())
        elements.append(Paragraph("3.  Room Matrix", styles["section_header"]))
        elements.append(HRFlowable(
            width="100%", thickness=0.5,
            color=SMARTCON_YELLOW, spaceAfter=6
        ))

        # Floor summary table
        elements.append(Paragraph("Floor Summary", styles["section_header"]))
        summary_data = [["Floor", "Room Count"]]
        total = 0
        for floor, count in sorted(floor_summary.items()):
            summary_data.append([f"Floor {floor}", str(count)])
            total += count
        summary_data.append(["TOTAL", str(total)])

        summary_table = Table(summary_data, colWidths=[2.0 * inch, 2.0 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  SMARTCON_GREEN),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("BACKGROUND",   (0, -1), (-1, -1), SMARTCON_YELLOW),
            ("FONTNAME",     (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, SMARTCON_LIGHT]),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 14))

        # Full room list by floor
        elements.append(Paragraph("Full Room List", styles["section_header"]))

        floors = sorted(set(r["floor"] for r in rooms))
        for floor in floors:
            floor_rooms = [str(r["room_number"]) for r in rooms if r["floor"] == floor]
            elements.append(Paragraph(f"Floor {floor}", styles["label"]))

            # Build rows of 10 rooms each
            row_size = 10
            room_rows = [floor_rooms[i:i+row_size] for i in range(0, len(floor_rooms), row_size)]

            # Pad last row
            for row in room_rows:
                while len(row) < row_size:
                    row.append("")

            room_table = Table(room_rows, colWidths=[0.65 * inch] * row_size)
            room_table.setStyle(TableStyle([
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, SMARTCON_LIGHT]),
                ("GRID",    (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
                ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME",(0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE",(0, 0), (-1, -1), 9),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(room_table)
            elements.append(Spacer(1, 8))     

    # --- BUILD ---
    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    print(f"\n[+] Report generated: {output_path}")
    return output_path