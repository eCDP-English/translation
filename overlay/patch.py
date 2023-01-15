#!/bin/python3
import json
import struct
import re
import argparse
import ndspy.rom
import ndspy.code

#this section of the rom contains strings for challenge the mcdonalds
#which this script should not touch at all
cmcd_ranges = [
	[0x00104620, 0x00104ACF],
	[0x001059E0, 0x0010A47F]
]

#sections in the memory that overlay files should not overwrite
protected_ranges = [
	[0x022544A0, 0x02254B3F]
]

def main(lang, rom_data, working_dir):

	json_names = []
	json_datas = []

	rom = ndspy.rom.NintendoDSRom(rom_data)
	overlays = rom.loadArm9Overlays()
	arm7 = rom.arm7
	a7_len = len(arm7)

	def read_jsonc(filepath:str):
		with open(filepath, 'r', encoding='utf-8') as f:
			text = f.read()
		re_text = re.sub(r'/\*[\s\S]*?\*/|//.*', '', text)
		json_obj = json.loads(re_text)
		return json_obj   

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

	#fills the specified area with null-bytes
	def fill(buffer, start, end):
		len = end - start + 1
		for i in range(0, len):
			buffer[start+i] = 0 

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
		section = read_jsonc(working_dir + "/data/" + name)
		text = read_jsonc(working_dir + "/" + lang + "/" + name)

		oid = section["id"]
		overlay = overlays[oid]
		
		data = overlay.data

		for string in section["strings"]:
			old_text = string["str"]
			old_blen = string["blen"]
			mem_addr = string["memory_address"]
			xrefs = string["xrefs"]
			ov_addr = mem_addr - overlay.ramAddress

			if str(ov_addr) in text.keys():
				new_text = text[str(ov_addr)]

				if old_text != new_text:
					text_sjis = new_text.encode("SHIFT_JIS")
					new_blen = len(text_sjis)+1
					print("Changing: "+old_text.replace("\n", "\\n")+" to "+new_text.replace("\n", "\\n"))
					if new_blen <= old_blen:
						print("Translated string is shorter, changing in-place")
						strcpy(text_sjis, data, ov_addr)
						fill(data, ov_addr+len(text_sjis)+1, ov_addr+old_blen)
					else:
						print("Translated string is longer, reallocating")
						fill(data, ov_addr, ov_addr+old_blen)

						new_mem_addr = len(arm7) + rom.arm7RamAddress

						if len(arm7) == a7_len:
							arm7.append(0)

						for b in text_sjis:
							arm7.append(b)
						arm7.append(0)

						for xref in xrefs:
							old_addr = struct.unpack("I", data[xref:xref+4])[0]
							if not old_addr == mem_addr:
								print("Address at "+hex(xref)+" is "+hex(old_addr)+" not "+hex(mem_addr)+" NOT CHANGING!")
								continue
							print("Changing "+hex(old_addr)+" to "+hex(new_mem_addr))
							new_addr = struct.pack("I", new_mem_addr)
							memcpy(new_addr, data, xref)
			else:
				print(old_text + " (" + str(ov_addr) + ") is missing from translation!")
			rom.files[overlay.fileID] = overlay.save()
					
	def read_jsons(jsonname):
		json_list = read_jsonc(jsonname)
		for json_name in json_list:
			json_datas.append(read_jsonc(working_dir + "/data/" + json_name))
			json_names.append(json_name)

	read_jsons(working_dir + "/files.json")
	for name in json_names:
		apply_mods(name)

	return bytearray(rom.save())

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
