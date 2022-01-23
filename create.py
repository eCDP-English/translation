#!/bin/python3
import os
import json
import struct
import hashlib
import ndspy.rom
import ndspy.code
import sys

from config import *

if len(sys.argv) >= 2:
	ROM_NAME = sys.argv[1]
	ROM_NAME = ROM_NAME.replace(".nds", "")
	ROM_NAME = ROM_NAME.replace(".NDS", "")

rom_bytes = open(ROM_NAME+".nds", "rb").read()
found_addresses = []

json_file_list = []

sections = []

# SCRIPT START

def find_in_rom(code_section):
	return rom_bytes.index(code_section)

def find_all(data, to_find):
	addresses = []
	baddr = 0
	while True:
		try:
			addr = (data.index(to_find))
			baddr += addr+len(to_find)
			data = data[baddr:]
			addresses.append(baddr-len(to_find))
		except ValueError:
			return addresses


def search_data(friendlyname, data, base_address):
	strBytes = b""
	memory_address = base_address
	new_mem = 0
	real_location = find_in_rom(data)
	strings = []
	for b in data:
		new_mem += 1
		if b == 0:
			offset = 0
			total_found = len(strBytes)
			while offset < total_found:
				obytes = strBytes[offset:]
				try:
					if check_valid(obytes) == True:
						strs = obytes.decode("SHIFT-JIS") 
						if len(strs) > 0: # No 0 width strings
							mloc = memory_address + offset
							# search entire code section for pointers
							ptr_locs = find_all(data, struct.pack("I", (mloc))) 
							if len(ptr_locs) > 0: # if found more than 0 pointers
								#absstr = "( ptr: "
								ptr_to_ptrs = []
								for ptr_loc in ptr_locs: # calculate real location of pointers in file
									ptr_to_ptr_loc = ptr_loc + real_location
									if ptr_to_ptr_loc in found_addresses: # have we seen this ptr be4?
										continue
									found_addresses.append(ptr_to_ptr_loc)
									ptr_to_ptrs.append(ptr_to_ptr_loc)
								if len(ptr_to_ptrs) > 0: # No real address ptr found?
									rom_address = (mloc - base_address)+real_location
									if rom_bytes[rom_address:rom_address+len(obytes)] == obytes:
										if not IGNORE_MD5:
											hstr = hashlib.md5(obytes).hexdigest()[:8]
											strings.append({"str":strs, "blen": len(obytes), "memory_address": mloc, "rom_address":rom_address, "md5": hstr, "xrefs":ptr_to_ptrs,"mod": None})
										else:
											strings.append({"str":strs, "blen": len(obytes), "memory_address": mloc, "rom_address":rom_address, "xrefs":ptr_to_ptrs,"mod": None})
				except UnicodeDecodeError:
					pass					
			
				offset += 1
			strBytes = b""
			memory_address += new_mem
			new_mem = 0
			continue
		strBytes += b.to_bytes(1, "little")
	data_info = {"name":friendlyname, "ram_loc":base_address, "file_loc": real_location, "length":len(data), "strings":strings}
	
	return data_info
		
		
def create_json(dinfo):
	
	# Merge original mods to new json!
	# (somehow, it is super complicated, dont try to make sense of it)
	for section in sections:
		if section["name"] == dinfo["name"]:
			for string in section["strings"]:
				if string["mod"] == None:
					continue
				else:
					added = False
					for dinfo_string in dinfo["strings"]:
						if dinfo_string["rom_address"] == string["rom_address"] and dinfo_string["memory_address"] == string["memory_address"]:
							dinfo_string["mod"] = string["mod"]
							added = True
							break
					if not added:
						dinfo["strings"].append(string)
	
	
	json_data = json.dumps(dinfo, indent=4, ensure_ascii=False)
	target_name = dinfo["name"]				

	found = False
	for json_file in json_file_list:
		found_name = json.loads(open(json_file, "rb").read())["name"]
		if found_name == target_name:
			open(json_file, "wb").write(bytes(json_data, "UTF-8"))
			found = True
			break
	if not found:
		open(target_name+".json", "wb").write(bytes(json_data, "UTF-8"))
		json_file_list.append(target_name+".json")
	
	
def read_jsons(json_name):
	json_files = json.loads(open(json_name, "rb").read())	
	for json_file in json_files:
		sections.append(json.loads(open(json_file, "rb").read()))
		json_file_list.append(json_file)
	

if os.path.exists(ROM_NAME + ".json"):
	read_jsons(ROM_NAME + ".json")
	
rom = ndspy.rom.NintendoDSRom.fromFile(ROM_NAME+".nds")
base_addr = rom.arm9RamAddress
arm9 = rom.loadArm9()

total_strings = 0

sectionId = 0
for section in arm9.sections:
	print("Scanning ARM9 Section: "+str(sectionId)+" .. ", end="", flush=True)
	dinfo = search_data("ARM9_"+str(sectionId), section.data, section.ramAddress)
	total_found = len(dinfo["strings"])
	total_strings += total_found
	print("Found "+str(total_found)+" Strings!", flush=True)
	
	create_json(dinfo)
	sectionId+=1
	
overlays = rom.loadArm9Overlays()
for oid, overlay in overlays.items():
	print("Scanning Overlay "+str(oid)+" .. ", end="", flush=True)
	dinfo = search_data("OVERLAY_"+str(oid), overlay.data, overlay.ramAddress)
	total_found = len(dinfo["strings"])
	total_strings += total_found
	print("Found "+str(total_found)+" Strings!", flush=True)
	
	create_json(dinfo)

jsonData = json.dumps(json_file_list, indent=4, ensure_ascii=False)
open(ROM_NAME+".json", "wb").write(bytes(jsonData, "UTF-8"))

print("Done! Found "+str(total_strings)+" strings in total!")
