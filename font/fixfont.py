#!/bin/python3
import os
import json
import struct
import hashlib
import ndspy.rom
import ndspy.code
import argparse

QUIZ_FONT = "data/minidata/font/LC12.NFTR"
REGULAR_FONT = "data/LCfont.NFTR"

def main(rom_data):
	rom = ndspy.rom.NintendoDSRom(rom_data)

	regularFont = rom.getFileByName(REGULAR_FONT)
	rom.setFileByName(QUIZ_FONT, regularFont)

	return bytearray(rom.save())

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("file", type=argparse.FileType("rb"), help = "ROM to insert texts in")
	args = parser.parse_args()

	rom_data = main(bytearray(args.file.read()))
	print("Patches done. writing to file.")

	fname = args.file.name
	open(fname[0:len(fname)-4] + "_patched.nds", "wb").write(rom_data)