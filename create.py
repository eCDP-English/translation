#!/bin/python3
import os
import json
import struct
import hashlib
import ndspy.rom
import ndspy.code

ROM_NAME = "ecdp"

rom_bytes = open(ROM_NAME+".nds", "rb").read()
master_strings = []
found_addresses = []
json_files = []

# custom rules
#customize values based on what you want
minimum_length = 3 #minimum length, in amount of bytes (not characters!)

range_ascii = [
	[0x0A, 0x0A], #newline (control char)

	#lets ignore these for now, we want full width strings
	#[0x30, 0x39], #numbers
	#[0x41, 0x5A], #uppercase alphabets
	#[0x61, 0x7A], #lowercase alphabets
]

range_sjis = [
	[0x824F, 0x8258], #numbers
	[0x8260, 0x8279], #uppercase alphabets
	[0x8281, 0x829A], #lowercase alphabets
	[0x829F, 0x82F1], #hiragana characters
	[0x8340, 0x8396], #katakana characters
	#kanjis
	[0x889F, 0x9872],
	[0x989F, 0x9FFC],
	[0xE040, 0xEAA4],
]

#always valid when a string starts with any of these
#(still goes through control character checks)
exceptions = [
	"SOC",
	"「"
]

#you probably don't want to edit this
control_chars = [
	[0x00, 0x09],
	[0x0B, 0x1F],
]

def check_valid(obytes):
	if len(obytes) < minimum_length:
		return False

	#check for control characters in the whole string
	i = 0
	while i < len(obytes):
		j = 0
		while j < len(control_chars):
			range = control_chars[j]
			if obytes[i] >= range[0] and obytes[i] <= range[1]:
				return False
			j += 1
		i += 1

	#exception checks
	str = obytes.decode("SHIFT-JIS")
	i = 0
	while i < len(exceptions):
		if (str.startswith(exceptions[i])):
			return True
		i += 1

	#doesn't need to check the whole string, garbage strings usually have invalid character at the start
	firstByte = obytes[0]
	secondByte = obytes[1]

	#check if it's a valid 1-byte character
	i = 0
	while i < len(range_ascii):
		range = range_ascii[i]

		if firstByte >= range[0] and firstByte <= range[1]:
			return True

		i += 1
	
	#check if it's a valid 2-byte character
	i = 0
	while i < len(range_sjis):
		range = range_sjis[i]
		byte = firstByte * 0x100 + secondByte

		if byte >= range[0] and byte <= range[1]:
			return True
		
		i += 1

	return False




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
	data_mod = {}
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
										strings.append({"str":strs, "blen": len(obytes), "memory_address": mloc, "rom_address":rom_address, "xrefs":ptr_to_ptrs})
										data_mod[str(rom_address)] = strs
				except UnicodeDecodeError:
					pass					
			
				offset += 1
			strBytes = b""
			memory_address += new_mem
			new_mem = 0
			continue
		strBytes += b.to_bytes(1, "little")
	data_info = {"name":friendlyname, "ram_loc":base_address, "file_loc": real_location, "length":len(data), "strings":strings}
	
	return [data_info, data_mod]
		
		
rom = ndspy.rom.NintendoDSRom.fromFile(ROM_NAME+".nds")
base_addr = rom.arm9RamAddress
arm9 = rom.loadArm9()

total_strings = 0

sectionId = 0
for section in arm9.sections:
	print("Scanning ARM9 Section: "+str(sectionId)+" .. ", end="", flush=True)
	data = search_data("ARM9_"+str(sectionId), section.data, section.ramAddress)
	dinfo = data[0]
	#master_strings.append(dinfo)
	total_found = len(dinfo["strings"])
	total_strings += total_found
	print("Found "+str(total_found)+" Strings!", flush=True)
	jsonData = json.dumps(dinfo, indent=4, ensure_ascii=False)
	jsonData_mod = json.dumps(data[1], indent=4, ensure_ascii=False)
	jsonName = "ARM9_"+str(sectionId)+".json"
	open("data/" + jsonName, "wb").write(bytes(jsonData, "UTF-8"))
	open("text_ja/" + jsonName, "wb").write(bytes(jsonData_mod, "UTF-8"))
	json_files.append(jsonName)
	sectionId+=1
	
overlays = rom.loadArm9Overlays()
for oid, overlay in overlays.items():
	print("Scanning Overlay "+str(oid)+" .. ", end="", flush=True)
	data = search_data("OVERLAY_"+str(oid), overlay.data, overlay.ramAddress)
	dinfo = data[0]
	#master_strings.append(dinfo)
	total_found = len(dinfo["strings"])
	total_strings += total_found
	print("Found "+str(total_found)+" Strings!", flush=True)
	jsonData = json.dumps(dinfo, indent=4, ensure_ascii=False)
	jsonData_mod = json.dumps(data[1], indent=4, ensure_ascii=False)
	jsonName = "OVERLAY_"+str(oid)+".json"
	open("data/" + jsonName, "wb").write(bytes(jsonData, "UTF-8"))
	open("text_ja/" + jsonName, "wb").write(bytes(jsonData_mod, "UTF-8"))
	json_files.append(jsonName)

jsonData = json.dumps(json_files, indent=4, ensure_ascii=False)
open(ROM_NAME+".json", "wb").write(bytes(jsonData, "UTF-8"))

print("Done! Found "+str(total_strings)+" strings in total!")
