import re
import json
import os

VENDOR_SIGNATURES = {
    "Honeywell INNCOM": [
        r"\bINNCOM\b", r"\bE7\b", r"\bEngINN\b",
        r"\bPC-503\b", r"\bPAN ID\b", r"\bRF Channel\b",
    ],
    "Verdant by Copeland": [
        r"\bVERDANT\b", r"\bVX4\b", r"\bCopeland\b",
        r"\bMesh ID\b", r"\bZbEE\b",
    ],
    "Telkonet EcoSmart PLUS": [
        r"\bEcoInsight\+?\b", r"\bEcoSource\+?\b",
        r"\bEcoSmart\b", r"\bNT8000\b", r"\bESU\b",
    ],
    "Telkonet EcoSmart Legacy": [
        r"\bEcoInsight\b", r"\bEcoSense\b",
        r"\bjn -t 120\b", r"\bda -I 6\b",
    ],
    "Telkonet Rhapsody / VDA Group": [
        r"\bRhapsody\b", r"\bTouch Combo\b",
        r"\bAida\b", r"\bES Controller\b",
        r"Rhapsody Commissioning App",
    ],
    "Interel GC Series": [
        r"\bINTEREL\b", r"\bGC3\b", r"\bGC4\b",
        r"\bICT\b", r"\bKNX\b",
    ],
}

VENDOR_PROFILE_MAP = {
    "Honeywell INNCOM":              "inncom.json",
    "Verdant by Copeland":           "verdant_vx4.json",
    "Telkonet EcoSmart PLUS":        "telkonet_ecosmart_plus.json",
    "Telkonet EcoSmart Legacy":      "telkonet_legacy.json",
    "Telkonet Rhapsody / VDA Group": "telkonet_ecosmart.json",
    "Interel GC Series":             "interel.json",
}

def detect_vendor(text):
    scores = {}
    for vendor, patterns in VENDOR_SIGNATURES.items():
        score = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
        if score > 0:
            scores[vendor] = score
    if not scores:
        return None, {}
    best = max(scores, key=scores.get)
    return best, scores

def detect_equipment_code(full_text):
    has_W1 = bool(re.search(r'\bW1\b', full_text))
    has_W2 = bool(re.search(r'\bW2\b', full_text))
    has_Y1 = bool(re.search(r'\bY1\b', full_text))
    has_Y2 = bool(re.search(r'\bY2\b', full_text))
    has_GL = bool(re.search(r'\bGL\b', full_text))
    has_GH = bool(re.search(r'\bGH\b', full_text))
    has_GM = bool(re.search(r'\bGM\b', full_text))
    has_OB = bool(re.search(r'\bO/?B\b', full_text))
    has_B  = bool(re.search(r'\bB\b', full_text))

    if has_Y2:           d1 = "5"
    elif has_Y1 and (has_OB or has_B): d1 = "1"
    elif has_Y1:         d1 = "2"
    else:                d1 = "0"

    if has_W2:           d2 = "5"
    elif has_W1:         d2 = "1"
    else:                d2 = "0"

    d3 = "1" if has_B and not has_OB else "0"

    if has_GL and has_GH and has_GM:   d4 = "3"
    elif has_GL and has_GH:            d4 = "2"
    elif has_GL or has_GH:             d4 = "1"
    else:                              d4 = "0"

    return f"{d1}{d2}{d3}{d4}"

def extract_all(full_text, detected_vendor):
    data = {
        "Hotel": "Not found", "City": "Not found",
        "Revision": "Not found", "Date": "Not found",
        "Drafter": "Not found", "Reviewer": "Not found",
        "Vendor": detected_vendor,
        "Thermostat_Model": "Not found",
        "HVAC_Description": "Not found",
        "HVAC_Model": "Not found",
        "Equipment_Code": "Not found",
        "Fan_Speed": "Not found",
        "Voltage": "Not found",
        "PMS": "Not found",
        "Occupied_Cool": "Not found",
        "Occupied_Heat": "Not found",
        "Unoccupied_Cool": "Not found",
        "Unoccupied_Heat": "Not found",
        "Grace_Period": "Not found",
        "Door_Locks": "Not specified",
        "Occupancy_Sensors": "Not found",
        "Door_Contact": "Not found",
        "Network_Type": "Not found",
        "PAN_ID": "Not found",
        "RF_Channel": "Not found",
        "CLI_Commands": [],
    }

    skip_words = ["DIAGRAM","DRAWING","SHEET","NETWORK","BUILDING","WIRING","REVISION","SMARTCON"]

    for pattern in [r'IHG\s*[-–]\s*([^\n]+)',r'MARRIOTT\s*[-–]?\s*([^\n]+)',
                    r'HILTON\s*[-–]?\s*([^\n]+)',r'HYATT\s*[-–]?\s*([^\n]+)',
                    r'DELTA\s*[-–]?\s*([^\n]+)',r'SHERATON\s*[-–]?\s*([^\n]+)']:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            data["Hotel"] = m.group(0).strip().split("\n")[0]
            break

    city_matches = re.findall(r'([A-Z][A-Za-z][\w\s]{2,25},\s*[A-Z]{2})', full_text)
    for match in city_matches:
        cleaned = match.strip()
        if any(w in cleaned.upper() for w in skip_words):
            continue
        if len(cleaned) < 35:
            data["City"] = cleaned
            break

    m = re.search(r'REVISION[:\s]+(\w+)', full_text, re.IGNORECASE)
    if m: data["Revision"] = m.group(1)

    m = re.search(r'DATE[:\s]+([0-9]{1,2}[-/][A-Z]{3,}[-/][0-9]{4})', full_text, re.IGNORECASE)
    if m: data["Date"] = m.group(1).strip()

    m = re.search(r'DRAFTER[:\s]+(\w+)', full_text, re.IGNORECASE)
    if m: data["Drafter"] = m.group(1)

    m = re.search(r'REVIEWER[:\s]+(\w+)', full_text, re.IGNORECASE)
    if m: data["Reviewer"] = m.group(1)

    if "Verdant" in detected_vendor:
        data["Equipment_Code"] = detect_equipment_code(full_text)

    for pattern in [r'(VX4-[\w-]+)', r'(GC[34][\w-]*)', r'(ECO[\w-]+)']:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            data["Thermostat_Model"] = m.group(1)
            break

    hvac_match = re.search(r'\b(FC4|FW2|FC2|PAC|HbW|HpB|HoW|HpO)\b', full_text)
    if hvac_match: data["HVAC_Description"] = hvac_match.group(1)

    m = re.search(r'(\d+\s*VAC)', full_text, re.IGNORECASE)
    if m: data["Voltage"] = m.group(1)

    fan_match = re.search(r'\b(LMh|LH|Lo)\b', full_text)
    if fan_match:
        data["Fan_Speed"] = fan_match.group(1)
    else:
        fan_match = re.search(r'(LOW[,/\s]*MED(?:IUM)?[,/\s]*HIGH|LOW/?HIGH)', full_text, re.IGNORECASE)
        if fan_match: data["Fan_Speed"] = fan_match.group(1).strip()

    m = re.search(r'PMS PROVIDER[:\s]+([^\n]+)', full_text, re.IGNORECASE)
    if m: data["PMS"] = m.group(1).strip()

    m = re.search(r'PAN ID[:\s]+(\d+)', full_text, re.IGNORECASE)
    if m: data["PAN_ID"] = m.group(1)

    m = re.search(r'RF Channel[:\s]+(\d+)', full_text, re.IGNORECASE)
    if m: data["RF_Channel"] = m.group(1)

    if re.search(r'VINGCARD', full_text, re.IGNORECASE):
        data["Door_Locks"] = "VingCard (Assa Abloy)"
    elif re.search(r'SAFLOK', full_text, re.IGNORECASE):
        data["Door_Locks"] = "Dormakaba Saflok"
    elif re.search(r'ONITY', full_text, re.IGNORECASE):
        data["Door_Locks"] = "Onity"
    elif re.search(r'DORMAKABA', full_text, re.IGNORECASE):
        data["Door_Locks"] = "Dormakaba"

    if re.search(r'ZIGBEE', full_text, re.IGNORECASE):
        data["Network_Type"] = "ZigBee Mesh"
    elif re.search(r'KNX', full_text, re.IGNORECASE):
        data["Network_Type"] = "KNX"

    return data

def load_vendor_profile(vendor_name):
    profile_file = VENDOR_PROFILE_MAP.get(vendor_name)
    if not profile_file:
        return None
    path = os.path.join("vendor_profiles", profile_file)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

    