#!/bin/python3
import os
import json
import struct
import hashlib
import ndspy.rom
import ndspy.code
import argparse

FONT_PATH = "LC12en.NFTR"
QUIZ_FONT = "data/minidata/font/LC12.NFTR"

def main(rom_data, working_dir):
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
	parser.add_argument("-wd", "--workingdir", dest = "dir", default = ".", help = "Working directory")
	args = parser.parse_args()

	rom_data = main(bytearray(args.file.read()), args.dir)
	print("Patches done. writing to file.")

	fname = args.file.name
	open(fname[0:len(fname)-4] + "_patched.nds", "wb").write(rom_data)