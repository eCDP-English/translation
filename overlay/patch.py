#!/bin/python3
import os
import json
import struct
import hashlib
import random
import argparse
#import ndspy.rom
#import ndspy.code

#this section of the rom contains strings for challenge the mcdonalds
#which this script should not touch at all
cmcd_ranges = [
	[0x00104620, 0x00104ACF],
	[0x001059E0, 0x0010A47F]
]


def main(lang, rom_data, working_dir):

	json_names = []
	json_datas = []

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

	def strcpy(new, buffer, offset):
		for i in range(0, len(new)):
			buffer[i+offset] = new[i]
		buffer[offset+len(new)] = 0 # write null-byte

	def memcpy(new, buffer, offset):
		for i in range(0, len(new)):
			buffer[i+offset] = new[i]
	
	def find_areas_with_zeros(section):
		start = section["file_loc"]
		end = start+section["length"]

		block = rom_data[start:end]

		zero_areas = []
		total_zeros = 0
		offset = 0
		for b in block:
			rom_address = (offset-total_zeros)+1
			valid = False
			if b == 0:
				for range in cmcd_ranges:
					if rom_address < range[0] or rom_address > range[1]:
						valid = True
			if valid:
				total_zeros += 1
			else:
				if not total_zeros <= 0:
					if not total_zeros-1 <= 0:
						zero_areas.append({"start": (offset-total_zeros)+1, "length": total_zeros-1})
				total_zeros = 0
			offset += 1
		return sorted(zero_areas, key=lambda d: d['length'], reverse=True) 
	

	def find_free_area(section, size):

		if not section["name"] == json_datas[0]["name"]: # First search in section 0! 
			location_in_arm9 = find_free_area(json_datas[0], size)
			if not location_in_arm9 == None:
				return location_in_arm9

		memory_address = section["ram_loc"]
		start = section["file_loc"]
		end = start+section["length"]

		block = rom_data[start:end]
		valid_locations = find_areas_with_zeros(section)
		for valid_location in valid_locations:
			can_use = True
			zstart = valid_location["start"]
			zlen = valid_location["length"]
			zend = zstart+zlen
			mloc = memory_address + zstart 

			for i in range(0, size): # try to find an area not in use
				pointers = find_all(block, struct.pack("I", (mloc+i)))
				if len(pointers) >= 1:
					can_use = False
					break
					
			if size >= zlen:
				continue
				
			if can_use == True:
				return (start + zstart, mloc)
			else:
				continue
				
		return None

	def apply_mods(name):
		section = json.loads(open(working_dir + "/data/" + name, "rb").read())
		text = json.loads(open(working_dir + "/" + lang + "/" + name, "rb").read())

		for string in section["strings"]:
			old_text = string["str"]
			old_blen = string["blen"]
			rom_addr = string["rom_address"]
			mem_addr = string["memory_address"]
			xrefs = string["xrefs"]

			og_bytes = rom_data[rom_addr:rom_addr+old_blen]

			if str(rom_addr) in text.keys():
				new_text = text[str(rom_addr)]

				if old_text != new_text:
					text_sjis = new_text.encode("SHIFT_JIS")
					new_blen = len(text_sjis)+1
					print("Changing: "+old_text+" to "+new_text)
					if new_blen <= old_blen:
						print(new_text + " is smaller than "+ old_text+". changing in-place")
						strcpy(text_sjis, rom_data, rom_addr)
					else:
						print(new_text + " is larger than "+old_text+" reallocating")
						print("Locating new area for text")
						new_file_addr, new_mem_addr = find_free_area(section, new_blen)
						print("Found : "+hex(new_file_addr)+", "+hex(new_mem_addr))
						strcpy(text_sjis, rom_data, new_file_addr)
						for xref in xrefs:
							old_addr = struct.unpack("I", rom_data[xref:xref+4])[0]
							if not old_addr == mem_addr:
								print("address at "+hex(xref)+" is "+hex(old_addr)+" not "+hex(mem_addr)+" NOT CHANGING!")
								continue
							print("Changing "+hex(old_addr)+" to "+hex(new_mem_addr))
							new_addr = struct.pack("I", new_mem_addr)
							memcpy(new_addr, rom_data, xref)
			else:
				print(old_text + " (" + str(rom_addr) + ") is missing from translation!")
					
	def read_jsons(jsonname):
		json_list = json.loads(open(jsonname, "rb").read())	
		for json_name in json_list:
			json_datas.append(json.loads(open(working_dir + "/data/" + json_name, "rb").read()))
			json_names.append(json_name)


	read_jsons(working_dir + "/files.json")
	for name in json_names:
		apply_mods(name)
	
	return rom_data

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("file", type=argparse.FileType("rb"), help = "ROM to insert texts in")
	parser.add_argument("-l", "--language", dest = "lang", default = "en", help = "Language to load translations from")
	parser.add_argument("-wd", "--workingdir", dest = "dir", default = ".", help = "Working directory (files.json and translations)")
	args = parser.parse_args()

	rom_data = main(args.lang, bytearray(args.file.read()), args.dir)
	print("Patches done. writing to file.")

	fname = args.file.name
	open(fname[0:len(fname)-4] + "_patched.nds", "wb").write(rom_data)
