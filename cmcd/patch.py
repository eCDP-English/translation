#!/bin/python3
import os
import re
import json
import ndspy.rom
import ndspy.code
import argparse

FONT_PATH = "LC12en.NFTR"
QUIZ_FONT = "data/minidata/font/LC12.NFTR"

def main(lang, rom_data, working_dir):
	def read_jsonc(filepath:str):
		with open(filepath, 'r', encoding='utf-8') as f:
			text = f.read()
		re_text = re.sub(r'/\*[\s\S]*?\*/|//.*', '', text)
		json_obj = json.loads(re_text)
		return json_obj   

	# patch strings
	json_data = read_jsonc(working_dir + "/data.json")
	json_strings = read_jsonc(working_dir + "/" + lang + ".json")

	for strdata in json_data:
		old_str = strdata["str"]
		old_blen = strdata["blen"]
		free_len = strdata["freelen"]
		rom_address = strdata["address"]
		new_str = json_strings[str(rom_address)]
		if old_str != new_str:
			print("Patching: " + new_str)
			new_str_bytes = new_str.encode("SHIFT_JIS")
			new_str_blen = len(new_str_bytes)
			if new_str_blen > free_len:
				raise Exception("Translated string is too long! Byte length: " + str(new_str_blen) + "/" + str(free_len))
			offset = 0
			for b in new_str_bytes:
				rom_data[rom_address + offset] = b
				offset += 1
			rom_data[rom_address + offset] = 0

    # patch: make monospace width smaller
	rom_data[0x000FAF78] = 0xF4
	rom_data[0x000FAF79] = 0x16

    # replace the CMCD font
	rom = ndspy.rom.NintendoDSRom(rom_data)

	with open(working_dir + "/" + FONT_PATH, "rb") as f:
		lc12en = f.read()
	
	rom.setFileByName(QUIZ_FONT, lc12en)

	return bytearray(rom.save())

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("file", type=argparse.FileType("rb"), help = "ROM to insert texts in")
	parser.add_argument("-l", "--language", dest = "lang", default = "en", help = "Language to load translations from")
	parser.add_argument("-wd", "--workingdir", dest = "dir", default = ".", help = "Working directory")
	args = parser.parse_args()

	rom_data = main(args.lang, bytearray(args.file.read()), args.dir)
	print("Patches done. writing to file.")

	fname = args.file.name
	open(fname[0:len(fname)-4] + "_patched.nds", "wb").write(rom_data)