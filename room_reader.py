import openpyxl
import os

def read_room_list(xlsx_path):
    """
    Reads a room list Excel file structured as floor columns.
    Each column is a floor, each row is a room number.
    Returns a flat list of room dictionaries and a summary.
    """

    if not os.path.exists(xlsx_path):
        print(f"[-] File not found: {xlsx_path}")
        return [], {}

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    rooms = []
    floor_summary = {}

    # Read all columns — each column is a floor
    for col in ws.iter_cols():
        floor_rooms = []

        for cell in col:
            val = cell.value

            # Skip None, skip formula strings, skip non-numeric
            if val is None:
                continue
            if isinstance(val, str) and val.startswith("="):
                continue
            if not isinstance(val, (int, float)):
                continue

            room_number = int(val)

            # Derive floor from first digit(s) of room number
            room_str = str(room_number)
            if len(room_str) == 3:
                floor = int(room_str[0])
            elif len(room_str) == 4:
                floor = int(room_str[:2])
            else:
                floor = 0

            floor_rooms.append({
                "room_number": room_number,
                "floor": floor,
            })

        if floor_rooms:
            floor_num = floor_rooms[0]["floor"]
            floor_summary[floor_num] = len(floor_rooms)
            rooms.extend(floor_rooms)

    return rooms, floor_summary


def print_room_summary(rooms, floor_summary, xlsx_path):
    print("\n" + "="*50)
    print("  ROOM LIST SUMMARY")
    print("="*50)
    print(f"  Source file  : {os.path.basename(xlsx_path)}")
    print(f"  Total rooms  : {len(rooms)}")
    print("-"*50)
    print("  Rooms per floor:")
    for floor, count in sorted(floor_summary.items()):
        print(f"    Floor {floor}  :  {count} rooms")
    print("-"*50)
    print("  Full room list:")
    for i, room in enumerate(rooms):
        print(f"    {room['room_number']}", end="  ")
        if (i + 1) % 10 == 0:
            print()
    print()
    print("="*50)


# =====================================================================
# RUN
# =====================================================================

if __name__ == "__main__":
    xlsx_path = input("Drop your room list Excel path here and press Enter: ").strip('"')
    rooms, floor_summary = read_room_list(xlsx_path)
    if rooms:
        print_room_summary(rooms, floor_summary, xlsx_path)