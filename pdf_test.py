import pdfplumber
import os
import re
import json
from generate_report import generate_report
from room_reader import read_room_list, print_room_summary


# =====================================================================
# VENDOR SIGNATURES — scoring system
# Add more patterns as you encounter new documents
# =====================================================================

VENDOR_SIGNATURES = {
    "Honeywell INNCOM": [
        r"\bINNCOM\b",
        r"\bE7\b",
        r"\bEngINN\b",
        r"\bPC-503\b",
        r"\bPAN ID\b",
        r"\bRF Channel\b",
        r"inncom\.com",
    ],
    "Verdant by Copeland": [
        r"\bVERDANT\b",
        r"\bVX4\b",
        r"\bVX-4\b",
        r"\bCopeland\b",
        r"\bMesh ID\b",
        r"\bZbEE\b",
        r"verdant\w*\.com",
    ],
    "Telkonet EcoSmart PLUS": [
        r"\bEcoInsight\+?\b",
        r"\bEcoSource\+?\b",
        r"\bEcoSmart\b",
        r"\bEcoContact\+?\b",
        r"\bEcoSense\+?\b",
        r"\bEcoSwitch\+?\b",
        r"\bNT8000\b",
        r"\bESU\b",
        r"telkonet\.com",
    ],
    "Telkonet EcoSmart Legacy": [
        r"\bEcoInsight\b",
        r"\bEcoSense\b",
        r"\bEcoSource\b",
        r"\bjn -t 120\b",
        r"\bda -I 6\b",
        r"\bGateway_MAC\b",
    ],
    "Telkonet Rhapsody / VDA Group": [
        r"\bRhapsody\b",
        r"\bTouch Combo\b",
        r"\bAida\b",
        r"\bES Controller\b",
        r"Rhapsody Commissioning App",
        r"\bVDA Group\b",
    ],
    "Interel GC Series": [
        r"\bINTEREL\b",
        r"\bEOS\s?2\.0\b",
        r"Interel\.IO",
        r"EOS Installer App",
        r"\bGC3\b",
        r"\bGC4\b",
        r"\bICT\b",
        r"\bKNX\b",
    ],
}

# =====================================================================
# VENDOR PROFILE MAP — links detected vendor to JSON file
# =====================================================================

VENDOR_PROFILE_MAP = {
    "Honeywell INNCOM":          "inncom.json",
    "Verdant by Copeland":       "verdant_vx4.json",
    "Telkonet EcoSmart PLUS":    "telkonet_ecosmart_plus.json",
    "Telkonet EcoSmart Legacy":  "telkonet_legacy.json",
    "Telkonet Rhapsody / VDA Group": "telkonet_ecosmart.json",
    "Interel GC Series":         "interel.json",
}

# =====================================================================
# EQUIPMENT CODE DETECTION (Verdant VX4)
# =====================================================================

def detect_equipment_code(full_text):
    has_W1 = bool(re.search(r'\bW1\b', full_text))
    has_W2 = bool(re.search(r'\bW2\b', full_text))
    has_Y1 = bool(re.search(r'\bY1\b', full_text))
    has_Y2 = bool(re.search(r'\bY2\b', full_text))
    has_GL = bool(re.search(r'\bGL\b', full_text))
    has_GH = bool(re.search(r'\bGH\b', full_text))
    has_GM = bool(re.search(r'\bGM\b', full_text))
    has_OB = bool(re.search(r'\bO/?B\b', full_text))
    has_B  = bool(re.search(r'\bB\b',   full_text))
    has_O  = bool(re.search(r'\bO\b',   full_text))

    if has_Y2:
        d1 = "5"
    elif has_Y1 and (has_OB or has_B):
        d1 = "1"
    elif has_Y1:
        d1 = "2"
    else:
        d1 = "0"

    if has_W2:
        d2 = "5"
    elif has_W1:
        d2 = "1"
    else:
        d2 = "0"

    if has_B and not has_OB:
        d3 = "1"
    else:
        d3 = "0"

    if has_GL and has_GH and has_GM:
        d4 = "3"
    elif has_GL and has_GH:
        d4 = "2"
    elif has_GL or has_GH:
        d4 = "1"
    else:
        d4 = "0"

    return f"{d1}{d2}{d3}{d4}"

# =====================================================================
# VENDOR DETECTION — scoring system
# =====================================================================

def detect_vendor(text):
    scores = {}
    for vendor, patterns in VENDOR_SIGNATURES.items():
        score = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
        if score > 0:
            scores[vendor] = score
    if not scores:
        return None, {}
    best_vendor = max(scores, key=scores.get)
    return best_vendor, scores

# =====================================================================
# SUBMITTAL EXTRACTION — pulls project data from PDF text
# =====================================================================

def extract_attributes(full_text, detected_vendor):
    data = {
        "Hotel":            "Not found",
        "City":             "Not found",
        "Revision":         "Not found",
        "Date":             "Not found",
        "Drafter":          "Not found",
        "Reviewer":         "Not found",
        "Vendor":           detected_vendor,
        "Thermostat_Model": "Not found",
        "HVAC_Description": "Not found",
        "HVAC_Model":       "Not found",
        "Equipment_Code":   "Not found",
        "Fan_Speed":        "Not found",
        "Voltage":          "Not found",
        "PMS":              "Not found",
        "Occupied_Cool":    "Not found",
        "Occupied_Heat":    "Not found",
        "Unoccupied_Cool":  "Not found",
        "Unoccupied_Heat":  "Not found",
        "Grace_Period":     "Not found",
        "Door_Locks":       "Not specified",
        "Occupancy_Sensors":"Not found",
        "Door_Contact":     "Not found",
        "Network_Type":     "Not found",
        "PAN_ID":           "Not found",
        "RF_Channel":       "Not found",
    }

    # Hotel name
    for pattern in [
        r'IHG\s*[-–]\s*([^\n]+)',
        r'MARRIOTT\s*[-–]?\s*([^\n]+)',
        r'HILTON\s*[-–]?\s*([^\n]+)',
        r'HYATT\s*[-–]?\s*([^\n]+)',
        r'WYNDHAM\s*[-–]?\s*([^\n]+)',
        r'DELTA\s*[-–]?\s*([^\n]+)',
        r'SHERATON\s*[-–]?\s*([^\n]+)',
        r'WESTIN\s*[-–]?\s*([^\n]+)',
        r'RADISSON\s*[-–]?\s*([^\n]+)',
    ]:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            data["Hotel"] = m.group(0).strip().split("\n")[0]
            break

   # City and state — skip lines with known document keywords
    skip_words = ["DIAGRAM", "DRAWING", "SHEET", "NETWORK", "BUILDING", "WIRING", "REVISION", "SMARTCON"]
    city_matches = re.findall(r'([A-Z][A-Za-z][\w\s]{2,25},\s*[A-Z]{2})', full_text)
    for match in city_matches:
        cleaned = match.strip()
        if any(word in cleaned.upper() for word in skip_words):
            continue
        if len(cleaned) < 35:
            data["City"] = cleaned
            break
        
    # Revision
    m = re.search(r'REVISION[:\s]+(\w+)', full_text, re.IGNORECASE)
    if m:
        data["Revision"] = m.group(1)

    # Date
    m = re.search(
        r'DATE[:\s]+([0-9]{1,2}[-/][A-Z]{3,}[-/][0-9]{4}|[A-Z]+ \d{1,2},\s*\d{4}|\d{2}-[A-Z]+-\d{4})',
        full_text, re.IGNORECASE)
    if m:
        data["Date"] = m.group(1).strip()

    # Drafter and reviewer
    m = re.search(r'DRAFTER[:\s]+(\w+)', full_text, re.IGNORECASE)
    if m:
        data["Drafter"] = m.group(1)

    m = re.search(r'REVIEWER[:\s]+(\w+)', full_text, re.IGNORECASE)
    if m:
        data["Reviewer"] = m.group(1)

    # Thermostat model
    for pattern in [
        r'(VX4-[\w-]+)',
        r'(GC[34][\w-]*)',
        r'(E[456789]-[\w-]+)',
        r'(ECO[\w-]+)',
    ]:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            data["Thermostat_Model"] = m.group(1)
            break

    # HVAC description
    m = re.search(r'DESCRIPTION[:\s]+([^\n]+)', full_text, re.IGNORECASE)
    if m:
        data["HVAC_Description"] = m.group(1).strip()

    # HVAC model
    m = re.search(r'Model#?\s*([\w-]+)', full_text, re.IGNORECASE)
    if m:
        data["HVAC_Model"] = m.group(1).strip()

    # INNCOM HVAC type
    hvac_match = re.search(r'\b(FC4|FW2|FC2|PAC|HbW|HpB|HoW|HpO)\b', full_text)
    if hvac_match:
        data["HVAC_Description"] = hvac_match.group(1)

    # Voltage
    m = re.search(r'(\d+\s*VAC)', full_text, re.IGNORECASE)
    if m:
        data["Voltage"] = m.group(1)

    # Equipment code (Verdant only)
    if "Verdant" in detected_vendor:
        data["Equipment_Code"] = detect_equipment_code(full_text)

    # INNCOM fan speed
    fan_match = re.search(r'\b(LMh|LH|Lo)\b', full_text)
    if fan_match:
        data["Fan_Speed"] = fan_match.group(1)
    else:
        fan_match = re.search(
            r'(LOW[,/\s]*MED(?:IUM)?[,/\s]*HIGH|LOW/?HIGH|3-Speed|Single Speed)',
            full_text, re.IGNORECASE)
        if fan_match:
            data["Fan_Speed"] = fan_match.group(1).strip()

    # Setpoints
    m = re.search(r'COOLING[:\s]+([\d°F]+)', full_text, re.IGNORECASE)
    if m:
        data["Occupied_Cool"] = m.group(1)

    m = re.search(r'HEATING[:\s]+([\d°F]+)', full_text, re.IGNORECASE)
    if m:
        data["Occupied_Heat"] = m.group(1)

    m = re.search(r'UNOCCUPIED.*?COOLING[:\s]+([\d°F]+)', full_text, re.IGNORECASE | re.DOTALL)
    if m:
        data["Unoccupied_Cool"] = m.group(1)

    m = re.search(r'UNOCCUPIED.*?HEATING[:\s]+([\d°F]+)', full_text, re.IGNORECASE | re.DOTALL)
    if m:
        data["Unoccupied_Heat"] = m.group(1)

    # Grace period
    m = re.search(r'(\d+)\s*MINUTES?\s*\(?ADJ\)?', full_text, re.IGNORECASE)
    if m:
        data["Grace_Period"] = m.group(1) + " minutes"

    # PMS
    m = re.search(r'PMS PROVIDER[:\s]+([^\n]+)', full_text, re.IGNORECASE)
    if m:
        data["PMS"] = m.group(1).strip()

    # PAN ID and RF Channel (INNCOM)
    m = re.search(r'PAN ID[:\s]+(\d+)', full_text, re.IGNORECASE)
    if m:
        data["PAN_ID"] = m.group(1)

    m = re.search(r'RF Channel[:\s]+(\d+)', full_text, re.IGNORECASE)
    if m:
        data["RF_Channel"] = m.group(1)

    # Door locks
    if re.search(r'VINGCARD|VING CARD', full_text, re.IGNORECASE):
        data["Door_Locks"] = "VingCard (Assa Abloy)"
    elif re.search(r'SAFLOK', full_text, re.IGNORECASE):
        data["Door_Locks"] = "Dormakaba Saflok"
    elif re.search(r'ONITY', full_text, re.IGNORECASE):
        data["Door_Locks"] = "Onity"
    elif re.search(r'DORMAKABA|DORMA KABA', full_text, re.IGNORECASE):
        data["Door_Locks"] = "Dormakaba"
    elif re.search(r'SALTO', full_text, re.IGNORECASE):
        data["Door_Locks"] = "Salto"
    elif re.search(r'CELS|ELECTRONIC LOCK|DOOR LOCK MANAGEMENT', full_text, re.IGNORECASE):
        data["Door_Locks"] = "CELS - Brand not specified in submittal"

    # Occupancy sensors
    m = re.search(r'(ZX-AOS|PIR|ZX-[\w-]+|S541[\w-]*|K594[\w-]*)', full_text, re.IGNORECASE)
    if m:
        data["Occupancy_Sensors"] = m.group(1).strip()

    # Door contact
    if re.search(r'DOOR\s*(SWITCH|CONTACT|SENSOR|CONTACT\+)', full_text, re.IGNORECASE):
        data["Door_Contact"] = "Yes - specified in submittal"

    # Network type
    if re.search(r'ZIGBEE', full_text, re.IGNORECASE):
        data["Network_Type"] = "ZigBee Mesh"
    elif re.search(r'KNX', full_text, re.IGNORECASE):
        data["Network_Type"] = "KNX"
    elif re.search(r'BACNET', full_text, re.IGNORECASE):
        data["Network_Type"] = "BACnet"
    elif re.search(r'RS-?485', full_text, re.IGNORECASE):
        data["Network_Type"] = "RS-485"
    elif re.search(r'TCP/?IP', full_text, re.IGNORECASE):
        data["Network_Type"] = "TCP/IP"

    return data

# =====================================================================
# LOAD VENDOR PROFILE FROM JSON
# =====================================================================

def load_vendor_profile(vendor_name):
    profile_file = VENDOR_PROFILE_MAP.get(vendor_name)
    if not profile_file:
        return None
    profile_path = os.path.join("vendor_profiles", profile_file)
    if not os.path.exists(profile_path):
        print(f"[-] Profile file not found: {profile_file}")
        return None
    with open(profile_path, "r") as f:
        return json.load(f)

# =====================================================================
# RUN
# =====================================================================

pdf_path = input("Drop your PDF path here and press Enter: ").strip('"')

if not os.path.exists(pdf_path):
    print("[-] Error: File not found. Check the path and try again.")
else:
    print("\n[*] Scanning all pages...")

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() or ""

    # Detect vendor
    detected_vendor, scores = detect_vendor(full_text)

    # Extract project attributes
    data = extract_attributes(full_text, detected_vendor or "Unknown")

    # Print extraction report
    print("\n" + "="*55)
    print("   SMARTCON SOLUTIONS - SUBMITTAL EXTRACTION REPORT")
    print("="*55)
    print(f"  Hotel              : {data['Hotel']}")
    print(f"  City               : {data['City']}")
    print(f"  Revision           : {data['Revision']}")
    print(f"  Date               : {data['Date']}")
    print(f"  Drafter            : {data['Drafter']}")
    print(f"  Reviewer           : {data['Reviewer']}")
    print("-"*55)
    print(f"  Vendor             : {data['Vendor']}")
    print(f"  Thermostat Model   : {data['Thermostat_Model']}")
    print(f"  Network Type       : {data['Network_Type']}")
    print("-"*55)
    print(f"  HVAC Description   : {data['HVAC_Description']}")
    print(f"  HVAC Model         : {data['HVAC_Model']}")
    print(f"  Voltage            : {data['Voltage']}")
    print(f"  Equipment Code     : {data['Equipment_Code']}")
    print(f"  Fan Speed          : {data['Fan_Speed']}")
    print("-"*55)
    print(f"  Occupied Cool      : {data['Occupied_Cool']}")
    print(f"  Occupied Heat      : {data['Occupied_Heat']}")
    print(f"  Unoccupied Cool    : {data['Unoccupied_Cool']}")
    print(f"  Unoccupied Heat    : {data['Unoccupied_Heat']}")
    print(f"  Grace Period       : {data['Grace_Period']}")
    print("-"*55)
    print(f"  PMS                : {data['PMS']}")
    print(f"  PAN ID             : {data['PAN_ID']}")
    print(f"  RF Channel         : {data['RF_Channel']}")
    print(f"  Door Locks         : {data['Door_Locks']}")
    print(f"  Occupancy Sensors  : {data['Occupancy_Sensors']}")
    print(f"  Door Contact       : {data['Door_Contact']}")
    print("="*55)

    # Print vendor detection scores
    print("\n[Vendor Detection Scores]")
    if scores:
        for v, s in sorted(scores.items(), key=lambda x: -x[1]):
            print(f"  {s} match(es) -> {v}")
    else:
        print("  No vendor signatures detected.")

    # Load and display matching commissioning profile
    if detected_vendor:
        print(f"\n[*] Loading commissioning profile for: {detected_vendor}")
        profile = load_vendor_profile(detected_vendor)
        if profile:
            print(f"  Platform : {profile.get('platform', 'N/A')}")
            print(f"  Tool     : {profile.get('software_tool', 'N/A')}")
            print(f"  Network  : {profile.get('network_address', 'N/A')}")
            print("\n[Binding Steps Available]")
            steps = profile.get("binding_steps", {})
            if isinstance(steps, dict):
                for section in steps:
                    print(f"  -> {section}")
            elif isinstance(steps, list):
                for i, step in enumerate(steps, 1):
                    print(f"  {i}. {step}")
    else:
        print("\n[-] No matching commissioning profile found.")
        print("    Check vendor signatures or add a new profile.")
        
      # --- ROOM LIST ---
    print("\n" + "="*55)
    print("  ROOM MATRIX INPUT")
    print("="*55)
    xlsx_input = input("Drop your room list Excel path here and press Enter (or press Enter to skip): ").strip('"')

    rooms = []
    floor_summary = {}

    if xlsx_input and os.path.exists(xlsx_input):
        rooms, floor_summary = read_room_list(xlsx_input)
        print_room_summary(rooms, floor_summary, xlsx_input)
    elif xlsx_input:
        print("[-] Excel file not found. Continuing without room list.")
    else:
        print("[*] No room list provided. Continuing without room matrix.")

    # --- GENERATE BRANDED PDF REPORT ---
    hotel_clean = data['Hotel'].replace(' ', '_').replace('/', '_')[:30]
    output_file = f"Smartcon_Field_Ops_{hotel_clean}.pdf"
    generate_report(data, profile, rooms, floor_summary, output_path=output_file)