#!/bin/python3
import os
import json
import struct
import hashlib
import re
import ndspy.rom
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--romname", dest = "romName", default = "ecdp", help = "Name of ROM to create files from")
args = parser.parse_args()

if args.romName:
	ROM_NAME = args.romName

rom = ndspy.rom.NintendoDSRom.fromFile(ROM_NAME+".nds")

folders = []
bins = []

targets = [
	"sec_tp",
    "sec_cp",
    "sec_dp",
	"ses_tp",
    "ses_cp",
    "ses_dp",
	"soc_tp",
	"soc_cp",
    "soc_dp",
	"soc_ap",
	"soc_mt",
]

if not os.path.exists("ja"):
	os.mkdir("ja")

for folder in rom.filenames.folders:
	validfiles = 0
	for file in folder[1].files:
		name = file.lower()
		if re.match(r".*\.(bin|[0-9]{3})", name):
			valid = False
			for t in targets:
				if name.startswith(t):
					valid = True
			if valid:
				bins.append(folder[0] + "/" + file)
				validfiles += 1
	if validfiles > 0:
		folders.append(folder[0])

for fld in folders:
	path = "ja/" + fld
	if not os.path.exists(path):
		os.mkdir(path)

def parseLEshort(bytes):
	return int.from_bytes(bytes, byteorder="little")

def getMetaData(data):
	numStrings=parseLEshort(data[0:2])
	offsets=[]
	for i in range(numStrings):
		offsets.append(parseLEshort(data[i*2+2:i*2+4]))
	return offsets	

def getStringAtOffset(data, offset):
	try:
		t=data[offset:data.index(b"\x00",offset)]
		return t.decode(encoding="shift-jisx0213")
	except Exception as err:
		print(offset, err)

strcount = 0
for bin in bins:
	print("Extracting text from: %s (%d)" % (bin, rom.filenames[bin]))
	file = rom.getFileByName(bin)

	offsets=getMetaData(file)
	strings=[]
	for i in offsets:
		strings.append(getStringAtOffset(file,i))
		strcount += 1

	jsonData = json.dumps(strings, indent=4, ensure_ascii=False)
	open("ja/" + bin + ".json", "wb").write(bytes(jsonData, "UTF-8"))

print("Done! Extracted %d strings in total!" % strcount)
