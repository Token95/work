import os
import uuid
import json
from flask import (
    Flask, render_template, request,
    redirect, url_for, send_file, session
)
from werkzeug.utils import secure_filename

# Import your existing engine modules
from pdf_test_core import extract_all, detect_vendor, load_vendor_profile
from room_reader import read_room_list
from generate_report import generate_report
from fieldwire_builder import build_fieldwire_project
from cli_generator import generate_cli_commands, DEVICE_PROFILES

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

ALLOWED_PDF   = {"pdf"}
ALLOWED_EXCEL = {"xlsx", "xls"}

def allowed_file(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

# =====================================================================
# HOME PAGE
# =====================================================================

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# =====================================================================
# PROCESS — runs the full engine
# =====================================================================

@app.route("/process", methods=["POST"])
def process():
    errors = []
    results = {}

    # --- GET FORM OPTIONS ---
    device_type   = request.form.get("device_type", "Touch Combo")
    light_wiring  = request.form.get("light_wiring", "NO")
    light_terminal= request.form.get("light_terminal", "W2")
    fan_stages    = int(request.form.get("fan_stages", 3))
    run_fieldwire = request.form.get("run_fieldwire") == "on"
    preparer      = request.form.get("preparer", "Smartcon Solutions")

    # --- HANDLE PDF UPLOAD ---
    pdf_path = None
    if "pdf_file" in request.files:
        pdf_file = request.files["pdf_file"]
        if pdf_file and allowed_file(pdf_file.filename, ALLOWED_PDF):
            filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            pdf_file.save(pdf_path)

    if not pdf_path:
        errors.append("No PDF file uploaded.")
        return render_template("index.html", errors=errors)

    # --- HANDLE EXCEL UPLOAD ---
    xlsx_path = None
    if "xlsx_file" in request.files:
        xlsx_file = request.files["xlsx_file"]
        if xlsx_file and xlsx_file.filename and allowed_file(xlsx_file.filename, ALLOWED_EXCEL):
            xfilename = secure_filename(xlsx_file.filename)
            xlsx_path = os.path.join(UPLOAD_FOLDER, xfilename)
            xlsx_file.save(xlsx_path)

    # --- EXTRACT PDF DATA ---
    import pdfplumber
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() or ""

    detected_vendor, scores = detect_vendor(full_text)
    data = extract_all(full_text, detected_vendor or "Unknown")

    # --- READ ROOM LIST ---
    rooms = []
    floor_summary = {}
    if xlsx_path:
        from room_reader import read_room_list, print_room_summary
        rooms, floor_summary = read_room_list(xlsx_path)

    # --- LOAD VENDOR PROFILE ---
    profile = None
    if detected_vendor:
        profile = load_vendor_profile(detected_vendor)

    # --- GENERATE CLI (Rhapsody only) ---
    cli_lines = []
    if detected_vendor and "Rhapsody" in detected_vendor:
        if light_wiring == "NC":
            DEVICE_PROFILES[device_type]["light_relay_terminal"] = light_terminal
        cli_lines = generate_cli_commands(
            extracted_data=data,
            device_type=device_type,
            light_wiring=light_wiring,
            fan_stages=fan_stages,
        )
        data["CLI_Commands"] = cli_lines

    # --- GENERATE PDF REPORT ---
    hotel_clean = data["Hotel"].replace(" ", "_").replace("/", "_")[:30]
    run_id      = str(uuid.uuid4())[:8]
    output_pdf  = os.path.join(OUTPUT_FOLDER, f"Smartcon_Field_Ops_{hotel_clean}_{run_id}.pdf")

    generate_report(
        data, profile, rooms, floor_summary,
        output_path=output_pdf,
        preparer=preparer
    )

    # --- GENERATE CLI TEXT FILE ---
    cli_file = None
    if cli_lines:
        cli_file = os.path.join(OUTPUT_FOLDER, f"CLI_{hotel_clean}_{run_id}.txt")
        with open(cli_file, "w") as f:
            for line in cli_lines:
                f.write(line + "\n")

    # --- FIELDWIRE DRY RUN ---
    fieldwire_summary = []
    if run_fieldwire and rooms:
        fieldwire_summary = build_fieldwire_project(
            data, rooms, floor_summary, dry_run=True
        )

    # --- RESULTS ---
    results = {
        "hotel":           data.get("Hotel", "Unknown"),
        "city":            data.get("City", "Unknown"),
        "vendor":          data.get("Vendor", "Unknown"),
        "thermostat":      data.get("Thermostat_Model", "Unknown"),
        "equipment_code":  data.get("Equipment_Code", "Unknown"),
        "fan_speed":       data.get("Fan_Speed", "Unknown"),
        "door_locks":      data.get("Door_Locks", "Unknown"),
        "pms":             data.get("PMS", "Unknown"),
        "room_count":      len(rooms),
        "floor_summary":   floor_summary,
        "scores":          scores,
        "output_pdf":      os.path.basename(output_pdf),
        "cli_file":        os.path.basename(cli_file) if cli_file else None,
        "cli_lines":       cli_lines,
        "preparer":        preparer,
    }

    return render_template("results.html", results=results)

# =====================================================================
# DOWNLOAD
# =====================================================================

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

# =====================================================================
# RUN
# =====================================================================

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True, port=5000)
    