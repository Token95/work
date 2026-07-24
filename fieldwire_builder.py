import os
import json
import requests
import datetime

# =====================================================================
# CONFIGURATION — paste your API key here when ready
# =====================================================================

FIELDWIRE_API_KEY = "YOUR_API_KEY_HERE"
FIELDWIRE_BASE_URL = "https://client-api.fieldwire.com/api/v3"

HEADERS = {
    "Fieldwire-Version": "2022-01-01",
    "Authorization": f"Token token={FIELDWIRE_API_KEY}",
    "Content-Type": "application/json",
}

# =====================================================================
# CHECKLIST TEMPLATES — vendor specific
# These will be expanded when you bring your checklist examples
# =====================================================================

CHECKLISTS = {

    # ----------------------------------------------------------------
    # SERVER — all vendors
    # ----------------------------------------------------------------
    "server": [
        "Install Server in Rack Space provided by PM",
        "Confirm Server remote communication",
        "Connect PMS Serial Interface if Applicable",
        "Confirm Server and Thermostat communication",
        "Confirm PMS Communication with Server",
    ],

    # ----------------------------------------------------------------
    # EDGE ROUTER — INNCOM
    # ----------------------------------------------------------------
    "edge_router_inncom": [
        "Install edge router",
        "Connect edge router to port and switch provided by PM",
        "Confirm edge router is communicating with server",
        "Confirm edge router is communicating with thermostats",
        "Confirm two-way communication between thermostats and edge router by changing a guest room temperature setting on each edge router",
        "Take picture of edge router and document location",
    ],

    # ----------------------------------------------------------------
    # GATEWAY — Telkonet
    # ----------------------------------------------------------------
    "gateway_telkonet": [
        "Install Gateway",
        "Confirm Gateway communicating with Server",
        "Confirm Gateway Pairs to Thermostats",
        "Confirm Gateway shows in EcoCentral",
    ],

    # ----------------------------------------------------------------
    # GATEWAY — Telkonet Kalahari style
    # ----------------------------------------------------------------
    "gateway_telkonet_full": [
        "Install Gateway",
        "Confirm Gateway communicating with Server",
        "Confirm Gateway Pairs to Thermostats",
        "Confirm Gateway shows in EcoCentral",
        "Pair Living Room Thermostat to Gateway",
        "Pair Primary Bedroom Thermostat to Gateway",
        "Pair Secondary Bedroom Thermostat to Gateway",
    ],

    # ----------------------------------------------------------------
    # ROOM — INNCOM Standard (Lock, Occ, AO Lighting, One Fan Speed)
    # ----------------------------------------------------------------
    "room_inncom_standard": [
        "Confirm Thermostat installed correctly",
        "Confirm Room Number is correct on thermostat",
        "Confirm PAN ID is correct on thermostat",
        "Confirm RF Channel is correct on thermostat",
        "Bind Occupancy Sensor to thermostat (If Applicable)",
        "Confirm Occupancy Sensor is communicating with thermostat (If Applicable)",
        "Bind Door Lock to thermostat",
        "Confirm Door Lock is communicating with thermostat",
        "Using Enginn - Write Configuration to thermostat",
        "Confirm Heat Call (Thermostat switches to heating and hot air is blowing from unit)",
        "Confirm Cool Call (Thermostat switches to cooling and cold air is blowing from unit)",
        "Confirm Fan High Call (In both Heating and Cooling, confirm High fan is working)",
        "Confirm Fan Low Call (In both Heating and Cooling, confirm Low fan is working)",
        "Using Sneezer - Unoccupied Lighting Test (Room is unoccupied and lights turn off)",
        "Using Sneezer - Occupied Lighting Test (Room is occupied and lights turn on)",
        "Using Sneezer - Change room to Unsold and back to Sold (Confirm setpoint returns to 72 when in sold)",
        "Take Picture of Thermostat",
        "Take Picture of Occupancy Sensor (If Applicable)",
    ],

    # ----------------------------------------------------------------
    # ROOM — INNCOM 2 Fan OCC DL Lighting
    # ----------------------------------------------------------------
    "room_inncom_2fan": [
        "Confirm Thermostat is Installed",
        "Confirm Room ID on thermostat",
        "Confirm PAN on thermostat",
        "Confirm RF Channel on Thermostat",
        "Bind Door Lock to Thermostat",
        "Confirm Door Lock communicating with Thermostat",
        "Bind Occupancy Sensor to Thermostat",
        "Confirm Occupancy Sensor communicating with Thermostat",
        "Confirm Heat Call",
        "Confirm Cool Call",
        "Confirm High Fan Call",
        "Confirm Medium Fan Call",
        "Confirm Low Fan Call",
        "Occupied Lighting Test (Lights are on when room is occupied)",
        "Unoccupied Lighting Test (Lights turn off when room goes unoccupied)",
    ],

    # ----------------------------------------------------------------
    # ROOM — INNCOM Friedrich AO Lighting DL OCC
    # ----------------------------------------------------------------
    "room_inncom_friedrich": [
        "Confirm Thermostat installed correctly",
        "Confirm PC502 installed correctly",
        "Confirm B485 Logic Board installed correctly",
        "Confirm Room Number is correct on thermostat",
        "Confirm PAN ID is correct on thermostat",
        "Confirm RF Channel is correct on thermostat",
        "Load Friedrich Firmware to PC502 (ST Link Tool)",
        "Bind PC502 to thermostat",
        "Confirm PC502 is communicating with thermostat",
        "Bind Occupancy Sensor to thermostat",
        "Confirm Occupancy Sensor is communicating with thermostat",
        "Bind Door Lock to thermostat",
        "Using Enginn - Write Configuration to Thermostat",
        "Using Enginn - Write Configuration to PC502",
        "Confirm Door Lock is communicating with thermostat",
        "Confirm Heat Call (Thermostat switches to heating and hot air is blowing from unit)",
        "Confirm Cool Call (Thermostat switches to cooling and cold air is blowing from unit)",
        "Confirm Fan High Call (In both Heating and Cooling, confirm High fan is working)",
        "Confirm Fan Medium Call (In both Heating and Cooling, confirm Medium fan is working)",
        "Confirm Fan Low Call (In both Heating and Cooling, confirm Low fan is working)",
        "Using Sneezer - Unoccupied Lighting Test (Room is unoccupied and lights turn off)",
        "Using Sneezer - Occupied Lighting Test (Room is occupied and lights turn on)",
        "Using Sneezer - Change room to Unsold and back to Sold (Confirm setpoint returns to 72 when in sold)",
        "Take Picture of Thermostat",
        "Take Picture of Occupancy Sensor (If Applicable)",
        "Take Picture of PC502 and B485",
    ],

    # ----------------------------------------------------------------
    # ROOM — INNCOM Simple (Spotsylvania style)
    # ----------------------------------------------------------------
    "room_inncom_simple": [
        "Install Thermostat",
        "Push New Config Through Enginn",
        "Bind Occupancy Sensor if Applicable (Adr 189)",
        "Confirm Occupancy Sensor Communication with Thermostat",
        "Bind Door Lock (Adr 67)",
        "Confirm Door Lock Communication with Thermostat",
        "Heating Test",
        "Cooling Test",
        "Fan Speed Test",
        "Light Test (Occupied) - Lights Turn On",
        "Lighting Test (Unoccupied) - Lights Turn Off",
    ],

    # ----------------------------------------------------------------
    # ROOM — Telkonet EcoInsight (Spotsylvania style)
    # ----------------------------------------------------------------
    "room_telkonet_ecosmart": [
        "Confirm Thermostat installed per Smartcon Submittal",
        "Confirm Occupancy Sensor installed per Smartcon Submittal",
        "Confirm Legrand Switch Installed Per Submittal",
        "Pair Living Room Thermostat to Gateway",
        "Pair Primary Bedroom Thermostat to Gateway",
        "Pair Secondary Bedroom Thermostat to Gateway",
        "Pair Door Lock to Living Room Thermostat (Slot 1)",
        "Pair Legrand Switch to Living Room Thermostat (Slot 2)",
        "Pair Occupancy Sensor to Living Room Thermostat (Slot 3)",
        "Heating Test - Confirm Heating works on thermostat and all three fan speeds work in heating",
        "Cooling Test - Confirm Cooling works on thermostat and all three fan speeds work in cooling",
        "Low Fan Test - Confirm Low fan works",
        "Medium Fan Test - Confirm Medium fan works",
        "High Fan Test - Confirm High fan works",
        "Occupied Lighting Test - Confirm when room is occupied light works",
    ],

    # ----------------------------------------------------------------
    # ROOM — Telkonet Rhapsody / AIDA / ES Controller
    # ----------------------------------------------------------------
    "room_telkonet_rhapsody": [
        "Load Thermostat Profile (Kivy APP)",
        "Load Room Number to Thermostat",
        "Run CLI on ESP tab in Kivy App (Do not use MISC Tab): zb -a 0x0201 0xf090 1",
        "Pair Door Lock (Slot 1)",
        "Confirm Door Lock Communication with Thermostat",
        "Pair Switch (Slot 2)",
        "Confirm Switch Communication with Thermostat",
        "Pair Occupancy Sensor 1 (Slot 3)",
        "Confirm Occupancy Sensor Communication with Thermostat",
        "Confirm Thermostat reporting in Rhapsody",
        "Confirm Door Lock Reporting in Rhapsody",
        "Confirm Switch Reporting in Rhapsody",
        "Heating Test",
        "Cooling Test",
        "High Fan Test",
        "Low Fan Test",
    ],

    # ----------------------------------------------------------------
    # ROOM — Verdant VX4
    # ----------------------------------------------------------------
    "room_verdant": [
        "Confirm MESH ID is correct",
        "Confirm Room Number is correct",
        "Confirm Equipment Code is correct",
        "Set OCC output to NO",
        "Pair Entry Occupancy Sensor to thermostat",
        "Confirm Occupancy Sensor communication to thermostat",
        "Confirm Heating Call - Thermostat goes into heating and hot air blows",
        "Confirm Cooling Call - Thermostat goes into cooling and cold air blows",
        "Confirm Fan High Call - Thermostat turns high fan on",
        "Confirm Fan Low Call - Thermostat turns low fan on",
        "Confirm Lighting Unoccupied - Room goes unoccupied and lights turn off",
        "Confirm Lighting Occupied - Room goes occupied and lights turn on",
        "Take Picture of Thermostat on Wall",
        "Take Picture of Entry Occupancy Sensor",
    ],

    # ----------------------------------------------------------------
    # ROOM — Verdant HP 2 Fan Lighting
    # ----------------------------------------------------------------
    "room_verdant_hp_2fan": [
        "Confirm MESH ID is correct",
        "Confirm Room Number is correct",
        "Confirm Equipment Code is correct",
        "Set OCC output to NO",
        "Pair Entry Occupancy Sensor to thermostat",
        "Confirm Occupancy Sensor communication to thermostat",
        "Confirm Heating Call - Thermostat goes into heating and hot air blows",
        "Confirm Cooling Call - Thermostat goes into cooling and cold air blows",
        "Confirm Fan High Call - Thermostat turns high fan on",
        "Confirm Fan Low Call - Thermostat turns low fan on",
        "Confirm Lighting Unoccupied - Room goes unoccupied and lights turn off",
        "Confirm Lighting Occupied - Room goes occupied and lights turn on",
        "Take Picture of Thermostat on Wall",
        "Take Picture of Entry Occupancy Sensor",
    ],

}
# =====================================================================
# VENDOR TO ROOM CHECKLIST MAP
# =====================================================================

VENDOR_CHECKLIST_MAP = {
    "Honeywell INNCOM":              "room_inncom_standard",
    "Verdant by Copeland":           "room_verdant",
    "Telkonet EcoSmart PLUS":        "room_telkonet_ecosmart",
    "Telkonet EcoSmart Legacy":      "room_telkonet_ecosmart",
    "Telkonet Rhapsody / VDA Group": "room_telkonet_rhapsody",
    "Interel GC Series":             "room_inncom_standard",
}

VENDOR_GATEWAY_MAP = {
    "Honeywell INNCOM":              "edge_router_inncom",
    "Verdant by Copeland":           None,
    "Telkonet EcoSmart PLUS":        "gateway_telkonet",
    "Telkonet EcoSmart Legacy":      "gateway_telkonet",
    "Telkonet Rhapsody / VDA Group": "gateway_telkonet",
    "Interel GC Series":             None,
}
# =====================================================================
# API CALLS
# =====================================================================

def create_project(hotel_name, city):
    project_name = f"{hotel_name} - {city} - Smartcon Commissioning"
    payload = {
        "project": {
            "name": project_name[:100],
            "description": (
                f"Generated by Smartcon Field Operations Engine\n"
                f"Date: {datetime.date.today().strftime('%B %d, %Y')}"
            ),
        }
    }
    response = requests.post(
        f"{FIELDWIRE_BASE_URL}/projects",
        headers=HEADERS,
        json=payload,
    )
    if response.status_code in [200, 201]:
        project = response.json()
        print(f"[+] Fieldwire project created: {project['name']}")
        return project["id"]
    else:
        print(f"[-] Failed to create project: {response.status_code} {response.text}")
        return None


def create_task(project_id, task_name, checklist_items, tag=None):
    payload = {
        "task": {
            "name": task_name,
            "checklist_items": [
                {"description": item, "completed": False}
                for item in checklist_items
            ],
        }
    }
    if tag:
        payload["task"]["tags"] = [tag]

    response = requests.post(
        f"{FIELDWIRE_BASE_URL}/projects/{project_id}/tasks",
        headers=HEADERS,
        json=payload,
    )
    if response.status_code in [200, 201]:
        task = response.json()
        print(f"  [+] Task created: {task_name}")
        return task["id"]
    else:
        print(f"  [-] Failed: {task_name} — {response.status_code}")
        return None

# =====================================================================
# FULL PROJECT BUILDER
# =====================================================================

def build_fieldwire_project(extracted_data, rooms, floor_summary, dry_run=True):
    """
    dry_run=True  prints what WOULD be created without calling the API.
    dry_run=False actually calls the Fieldwire API.
    """

    hotel    = extracted_data.get("Hotel", "Unknown Property")
    city     = extracted_data.get("City", "Unknown City")
    vendor   = extracted_data.get("Vendor", "Unknown")
    revision = extracted_data.get("Revision", "N/A")

    room_checklist_key = VENDOR_CHECKLIST_MAP.get(vendor, "room_verdant")

    print("\n" + "="*55)
    print("  FIELDWIRE PROJECT BUILDER")
    print("="*55)
    print(f"  Hotel   : {hotel}")
    print(f"  City    : {city}")
    print(f"  Vendor  : {vendor}")
    print(f"  Rooms   : {len(rooms)}")
    print(f"  Mode    : {'DRY RUN - no API calls' if dry_run else 'LIVE - calling Fieldwire API'}")
    print("="*55)

    if dry_run:
        # Print full task plan without calling API
        print("\n[DRY RUN] Tasks that will be created:\n")

        print("  INFRASTRUCTURE")
        print(f"    Task: Server Setup ({len(CHECKLISTS['server'])} checklist items)")
        for item in CHECKLISTS["server"]:
            print(f"      □ {item}")

        print()
        gateway_key = VENDOR_GATEWAY_MAP.get(vendor)
        if gateway_key:
            gateway_checklist = CHECKLISTS[gateway_key]
            for floor in sorted(floor_summary.keys()):
                print(f"    Task: Edge Router / Gateway - Floor {floor} ({len(gateway_checklist)} checklist items)")
                for item in gateway_checklist:
                    print(f"      □ {item}")
        else:
            print(f"    No gateway tasks for {vendor}")

        print(f"\n  ROOMS ({len(rooms)} total)")
        checklist = CHECKLISTS[room_checklist_key]
        cli_commands = extracted_data.get("CLI_Commands", [])
        cli_items = [
            line for line in cli_commands
            if line.strip() and not line.startswith("#")
        ]

        for room in rooms[:3]:
            full_checklist = checklist + (
                ["--- CLI COMMANDS ---"] + cli_items
                if cli_items else []
            )
            print(f"    Task: Room {room['room_number']} - Floor {room['floor']} ({len(full_checklist)} checklist items)")
            for item in checklist:
                print(f"      □ {item}")
            if cli_items:
                print(f"      --- CLI COMMANDS ---")
                for cmd in cli_items:
                    print(f"      > {cmd}")
        if len(rooms) > 3:
            print(f"    ... and {len(rooms) - 3} more rooms following the same pattern")

        print(f"\n[DRY RUN COMPLETE]")
        print(f"  Total tasks that will be created: {1 + len(floor_summary) + len(rooms)}")
        print(f"  Server tasks     : 1")
        print(f"  Edge router tasks: {len(floor_summary)}")
        print(f"  Room tasks       : {len(rooms)}")

    else:
        # LIVE API CALLS
        if FIELDWIRE_API_KEY == "YOUR_API_KEY_HERE":
            print("[-] API key not set. Add your Fieldwire API key to fieldwire_builder.py")
            return

        project_id = create_project(hotel, city)
        if not project_id:
            return

        # Server task
        create_task(project_id, "Server Setup", CHECKLISTS["server"], tag="Infrastructure")

        # Edge router tasks per floor
        for floor in sorted(floor_summary.keys()):
            task_name = f"Edge Router - Floor {floor}"
            create_task(project_id, task_name, CHECKLISTS["edge_router"], tag="Infrastructure")

        # Room tasks
        checklist = CHECKLISTS[room_checklist_key]
        cli_commands = extracted_data.get("CLI_Commands", [])
        cli_items = [
            line for line in cli_commands
            if line.strip() and not line.startswith("#")
        ]
        full_checklist = checklist + (
            ["--- CLI COMMANDS ---"] + cli_items if cli_items else []
        )
        for room in rooms:
            task_name = f"Room {room['room_number']} - Floor {room['floor']}"
            create_task(project_id, task_name, full_checklist, tag=f"Floor {room['floor']}")
            

        print(f"\n[+] Fieldwire project build complete.")
        print(f"  Total tasks created: {1 + len(floor_summary) + len(rooms)}")