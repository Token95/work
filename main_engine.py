import os
import json

def run_pipeline(hotel_name, vendor_file):
	profile_path = os.path.join("vendor_profiles", vendor_file)
		
	if not os.path.exists(profile_path):
		print(f"[-] Error: Profile '{vendor_file}' not found.")
		return
			
	with open(profile_path, "r") as file:
		data = json.load(file)
			
	print("\n" + "="*50)
	print(f"HOTEL: {hotel_name}")
	print(f"PLATFORM: {data['platform']}")
	print("="*50)
		
		
	print(f"\n[Configuration]")
	print(f"	Room Variable	: {data['room_variable']}")
	print(f"	Network Address	: {data['network_address']}")


	print(f"\n[Binding Steps]")
	if isinstance(data['binding_steps'], list):
		for index, step in enumerate(data['binding_steps'], start=1):
			print(f" {index}. {step}")
	elif isinstance(data['binding_steps'], dict):
		for section, steps in data['binding_steps'].items():
			print(f"\n -- {section.upper()} --")
			for index, step in enumerate(steps, start=1):
				print(f"	{index}. {step}")
					
					
# Swap the active profile below to change vendor behavior:
chosen_profile = "inncom.json"
# chosen_profile = "telkonet_legacy.json"
# chosen_profile = "verdant_vx4.json"

run_pipeline(hotel_name="Marriott", vendor_file=chosen_profile)

