#!/bin/python3
import os
import json
import struct
import hashlib
import ndspy.rom
import ndspy.code
import argparse

def main(lang, rom_data, working_dir):
	rom = ndspy.rom.NintendoDSRom(rom_data)

	def LEshort(num):
		lower=num%256
		higher=num//256
		return bytes([lower,higher])

	for folder in os.listdir(working_dir + "/" + lang):
		for file in os.listdir(working_dir + "/" + lang + "/" + folder):
			rom_filename = folder + "/" + file[0:len(file)-5]
			strings = json.loads(open("%s/%s/%s/%s" % (working_dir, lang, folder, file), "rb").read())

			print("Compiling: %s (%d)" % (rom_filename, rom.filenames[rom_filename]))

			stringBytes = []
			for i in strings:
				stringBytes.append(i.encode(encoding="shift-jisx0213")+b"\x00")

			numStrings=len(strings)
			offset=2*(numStrings+1)

			t=b""
			t+=LEshort(numStrings)
			for i in stringBytes:
				t+=LEshort(offset)
				offset+=len(i)
			for i in stringBytes:
				t+=i

			rom.setFileByName(rom_filename, t)

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