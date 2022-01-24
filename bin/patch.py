#!/bin/python3
import os
import json
import struct
import hashlib
import ndspy.rom
import ndspy.code

ROM_NAME = "ecdp"
LANG = "en"

rom = ndspy.rom.NintendoDSRom.fromFile(ROM_NAME+".nds")

def LEshort(num):
	lower=num%256
	higher=num//256
	return bytes([lower,higher])

for folder in os.listdir(LANG):
	for file in os.listdir(LANG + "/" + folder):
		rom_filename = folder + "/" + file[0:len(file)-5]
		strings = json.loads(open("%s/%s/%s" % (LANG, folder, file), "rb").read())

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

print("Patches done. writing to file.")
open(ROM_NAME + "_patched.nds", "wb").write(rom.save())
