#!/bin/python3
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("file", type=argparse.FileType("rb"), help = "ROM to extract texts from")
args = parser.parse_args()

rom_bytes = args.file.read()

data_json = []
strings_json = {}

#ROM file address range of where challenge the mcdonalds strings are stored at
cmcd_ranges = [
	[0x00104620, 0x00104ACF],
	[0x001059E0, 0x0010A47F]
]

for range in cmcd_ranges:
	cmcd_data = rom_bytes[range[0]:range[1]]
	str_bytes = bytearray()
	addr = 0
	free_len = 0
	str_found = False
	count_len = False

	def write_data():
		global free_len
		free_len -= 1
		string = str_bytes.decode("SHIFT-JIS")
		data_json.append({
			"str": string,
			"blen": len(str_bytes),
			"freelen": free_len,
			"address": addr
		})
		strings_json[str(addr)] = string
		print("FREE END : LEN " + str(free_len))

	offset = 0
	for b in cmcd_data:
		if b != 0 and str_found == False:
			if count_len == True:
				write_data()
			count_len = True
			free_len = 0
			str_found = True
			str_bytes = bytearray()
			addr = range[0] + offset
			print("START")
		if b != 0 and str_found == True:
			str_bytes.append(b)
		if count_len == True:
			free_len += 1
		if b == 0 and str_found == True:
			str_found = False
			print("End")
			print(str_bytes.decode("SHIFT-JIS"))
		offset += 1
	if count_len == True:
		write_data()

jdata = json.dumps(data_json, indent=4, ensure_ascii=False)
jstrs = json.dumps(strings_json, indent=4, ensure_ascii=False)

open("data.json", "wb").write(bytes(jdata, "UTF-8"))
open("ja.json", "wb").write(bytes(jstrs, "UTF-8"))