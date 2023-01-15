#!/bin/python3
import os
import json
import struct
import hashlib
import ndspy.rom
import ndspy.code
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("file", type=argparse.FileType("rb"), help = "ROM to extract texts from")
args = parser.parse_args()

rom_bytes = args.file.read()
rom = ndspy.rom.NintendoDSRom(rom_bytes)
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
exceptions_start = [
	"SOC",
	"UHC",
	"HLZ",
	"「",
	"○○円",
]

#always valid when a string ends with any of these
#(still goes through control character checks)
exceptions_end = [
]

#always valid when a string equals to any of these
#this ignores the length check
#(still goes through control character checks)
exceptions_single = [
]

#this section of the rom contains strings for challenge the mcdonalds
#which this script should not touch at all
cmcd_ranges = [
	[0x00104620, 0x00104ACF],
	[0x001059E0, 0x0010A47F]
]

#you probably don't want to edit this
control_chars = [
	[0x00, 0x09],
	[0x0B, 0x1F],
]

def check_valid(obytes):
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

	str = obytes.decode("SHIFT-JIS")
	#exception checks 1
	i = 0
	while i < len(exceptions_single):
		if (str == exceptions_single[i]):
			return True
		i += 1

	if len(obytes) < minimum_length:
		return False

	#exception checks 2
	i = 0
	while i < len(exceptions_start):
		if (str.startswith(exceptions_start[i])):
			return True
		i += 1

	i = 0
	while i < len(exceptions_end):
		if (str.endswith(exceptions_end[i])):
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


def search_data(id, data, base_address):
	strBytes = b""
	memory_address = base_address
	new_mem = 0
	real_location = find_in_rom(data)
	strings = []
	data_mod = {}

	def read_jsonc(filepath:str):
		import re
		with open(filepath, 'r', encoding='utf-8') as f:
			text = f.read()
		re_text = re.sub(r'/\*[\s\S]*?\*/|//.*', '', text)
		json_obj = json.loads(re_text)
		return json_obj   

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
								rom_address = (mloc - base_address)+real_location
								valid = True
								for range in cmcd_ranges:
									if rom_address >= range[0] and rom_address <= range[1]:
										valid = False
								if valid == False:
									continue
								if rom_bytes[rom_address:rom_address+len(obytes)] == obytes:
									strings.append({"str":strs, "blen": len(obytes), "memory_address": mloc, "xrefs":ptr_locs})
									data_mod[str(mloc - base_address)] = strs
				except UnicodeDecodeError:
					pass					
			
				offset += 1
			strBytes = b""
			memory_address += new_mem
			new_mem = 0
			continue
		strBytes += b.to_bytes(1, "little")
	data_info = {"id": id, "length":len(data), "strings":strings}
	
	return [data_info, data_mod]
		
base_addr = rom.arm9RamAddress
arm9 = rom.loadArm9()

total_strings = 0

sectionId = 0
for section in arm9.sections:
	print("Scanning ARM9 Section: "+str(sectionId)+" .. ", end="", flush=True)
	data = search_data(sectionId, section.data, section.ramAddress)
	dinfo = data[0]
	#master_strings.append(dinfo)
	total_found = len(dinfo["strings"])
	total_strings += total_found
	print("Found "+str(total_found)+" Strings!", flush=True)
	jsonData = json.dumps(dinfo, indent=4, ensure_ascii=False)
	jsonData_mod = json.dumps(data[1], indent=4, ensure_ascii=False)
	jsonName = "ARM9_"+str(sectionId)+".json"
	open("data/" + jsonName, "wb").write(bytes(jsonData, "UTF-8"))
	open("ja/" + jsonName, "wb").write(bytes(jsonData_mod, "UTF-8"))
	json_files.append(jsonName)
	sectionId+=1

jsonData = json.dumps(json_files, indent=4, ensure_ascii=False)
open("files.json", "wb").write(bytes(jsonData, "UTF-8"))

print("Done! Found "+str(total_strings)+" strings in total!")
