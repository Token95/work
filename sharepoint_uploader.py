import os
import json
import requests
import msal
from smartcon_config import (
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE, PROJECTS_FOLDER
)

# =====================================================================
# SMARTCON SHAREPOINT UPLOADER
# Creates project folder structure and uploads commissioning files
# =====================================================================

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
AUTHORITY  = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES     = ["https://graph.microsoft.com/.default"]

# =====================================================================
# AUTHENTICATION
# =====================================================================

def get_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" in result:
        print("[+] Authenticated with Microsoft Graph")
        return result["access_token"]
    else:
        print(f"[-] Auth failed: {result.get('error_description')}")
        return None


def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
def get_current_user(token):
    """
    Pulls the display name and email of the logged-in
    Microsoft 365 account using the app token.
    Falls back to Windows login if Graph call fails.
    """
    url = f"{GRAPH_BASE}/users"
    params = {"$filter": f"mail eq 'dbrown@smartconsolutionsllc.com'",
              "$select": "displayName,mail"}
    r = requests.get(url, headers=get_headers(token), params=params)

    if r.status_code == 200:
        users = r.json().get("value", [])
        if users:
            name = users[0].get("displayName", "Unknown")
            email = users[0].get("mail", "")
            print(f"[+] Preparer: {name} ({email})")
            return name, email

    # Fallback to Windows login
    import os
    fallback = os.getlogin()
    print(f"[*] Using Windows login as fallback: {fallback}")
    return fallback, ""

# =====================================================================
# SITE AND DRIVE LOOKUP
# =====================================================================

def get_site_id(token):
    url = f"{GRAPH_BASE}/sites/{SHAREPOINT_HOSTNAME}:/sites/{SHAREPOINT_SITE}"
    r = requests.get(url, headers=get_headers(token))
    if r.status_code == 200:
        site_id = r.json()["id"]
        print(f"[+] Site found: {site_id}")
        return site_id
    else:
        print(f"[-] Site not found: {r.status_code} {r.text}")
        return None


def get_drive_id(token, site_id):
    url = f"{GRAPH_BASE}/sites/{site_id}/drives"
    r = requests.get(url, headers=get_headers(token))
    if r.status_code == 200:
        drives = r.json().get("value", [])
        for drive in drives:
            if "Documents" in drive.get("name", ""):
                print(f"[+] Drive found: {drive['name']}")
                return drive["id"]
        # fallback to first drive
        if drives:
            print(f"[+] Using drive: {drives[0]['name']}")
            return drives[0]["id"]
    print(f"[-] Drive not found: {r.status_code}")
    return None

# =====================================================================
# FOLDER MANAGEMENT
# =====================================================================

def get_or_create_folder(token, drive_id, parent_path, folder_name):
    """
    Check if folder exists under parent_path.
    Create it if it does not exist.
    Returns the folder item ID.
    """
    # Check if folder exists
    encoded = parent_path.replace(" ", "%20")
    url = f"{GRAPH_BASE}/drives/{drive_id}/root:/{encoded}/{folder_name}"
    r = requests.get(url, headers=get_headers(token))

    if r.status_code == 200:
        folder_id = r.json()["id"]
        print(f"[+] Folder exists: {folder_name}")
        return folder_id

    # Create the folder
    parent_url = f"{GRAPH_BASE}/drives/{drive_id}/root:/{encoded}:/children"
    parent_url = parent_url.replace("%20", " ")
    encoded_parent = parent_path.replace(" ", "%20")
    create_url = f"{GRAPH_BASE}/drives/{drive_id}/root:/{encoded_parent}:/children"

    payload = {
        "name":   folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename"
    }
    r2 = requests.post(
        create_url,
        headers=get_headers(token),
        json=payload
    )
    if r2.status_code in [200, 201]:
        folder_id = r2.json()["id"]
        print(f"[+] Folder created: {folder_name}")
        return folder_id
    else:
        print(f"[-] Failed to create folder {folder_name}: {r2.status_code} {r2.text}")
        return None


def build_project_folder(token, drive_id, hotel_name, city):
    """
    Creates this structure under Projects - SCS Internal/Current:
    ├── [Hotel Name] - [City]/
    │   └── Commissioning/
    Returns the commissioning folder path string.
    """
    # Clean hotel name for folder
    clean_hotel = hotel_name.replace("/", "-").replace("\\", "-").strip()
    clean_city  = city.replace("/", "-").strip() if city != "Not found" else ""

    if clean_city:
        project_folder_name = f"{clean_hotel} - {clean_city}"
    else:
        project_folder_name = clean_hotel

    # Trim to safe length
    project_folder_name = project_folder_name[:80]

    print(f"\n[*] Building folder structure for: {project_folder_name}")

    # Create project folder under Current
    project_id = get_or_create_folder(
        token, drive_id,
        PROJECTS_FOLDER,
        project_folder_name
    )
    if not project_id:
        return None, None

    # Create Commissioning subfolder
    project_path = f"{PROJECTS_FOLDER}/{project_folder_name}"
    comm_id = get_or_create_folder(
        token, drive_id,
        project_path,
        "Commissioning"
    )

    commissioning_path = f"{project_path}/Commissioning"
    return commissioning_path, comm_id

# =====================================================================
# FILE UPLOAD
# =====================================================================

def upload_file(token, drive_id, sharepoint_folder_path, local_file_path):
    """
    Uploads a local file to a SharePoint folder.
    """
    if not os.path.exists(local_file_path):
        print(f"[-] File not found: {local_file_path}")
        return False

    filename = os.path.basename(local_file_path)
    encoded_path = sharepoint_folder_path.replace(" ", "%20")
    upload_url = (
        f"{GRAPH_BASE}/drives/{drive_id}/root:/"
        f"{encoded_path}/{filename}:/content"
    )

    with open(local_file_path, "rb") as f:
        file_data = f.read()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/octet-stream",
    }

    r = requests.put(upload_url, headers=headers, data=file_data)

    if r.status_code in [200, 201]:
        web_url = r.json().get("webUrl", "")
        print(f"[+] Uploaded: {filename}")
        print(f"    URL: {web_url}")
        return True
    else:
        print(f"[-] Upload failed: {filename} — {r.status_code} {r.text[:200]}")
        return False

# =====================================================================
# MAIN UPLOAD FUNCTION
# =====================================================================

def upload_commissioning_package(extracted_data, output_files):
    """
    Main entry point.
    extracted_data: dict from pdf_test.py extraction
    output_files:   list of local file paths to upload

    Creates folder structure and uploads all files.
    """
    hotel = extracted_data.get("Hotel", "Unknown Property")
    city  = extracted_data.get("City",  "Unknown City")

    print("\n" + "="*55)
    print("  SMARTCON SHAREPOINT UPLOADER")
    print("="*55)
    print(f"  Hotel : {hotel}")
    print(f"  City  : {city}")
    print(f"  Files : {len(output_files)}")
    print("="*55)

    # Authenticate
    token = get_token()
    if not token:
        return False

    # Get site
    site_id = get_site_id(token)
    if not site_id:
        return False

    # Get drive
    drive_id = get_drive_id(token, site_id)
    if not drive_id:
        return False

    # Build folder structure
    comm_path, comm_id = build_project_folder(token, drive_id, hotel, city)
    if not comm_path:
        return False

    # Upload all files
    print(f"\n[*] Uploading {len(output_files)} file(s) to SharePoint...")
    success = 0
    for filepath in output_files:
        if filepath and os.path.exists(filepath):
            if upload_file(token, drive_id, comm_path, filepath):
                success += 1

    print(f"\n[+] Upload complete: {success}/{len(output_files)} files")
    print(f"[+] SharePoint path: {PROJECTS_FOLDER}/{hotel}/Commissioning")
    return True


# =====================================================================
# STANDALONE TEST
# =====================================================================

if __name__ == "__main__":
    test_data = {
        "Hotel": "IHG - Circa 39",
        "City":  "Miami Beach, FL",
    }
    test_files = []

    # Find any PDF or TXT in current folder to test with
    for f in os.listdir("."):
        if f.endswith(".pdf") or f.endswith(".txt"):
            test_files.append(f)
            if len(test_files) >= 2:
                break

    if test_files:
        upload_commissioning_package(test_data, test_files)
    else:
        print("[-] No test files found in current folder")