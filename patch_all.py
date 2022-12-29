#!/bin/python3
import bin.patch
import overlay.patch
import cmcd.patch
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("file", type=argparse.FileType("rb"), help = "ROM to extract texts from")
parser.add_argument("-l", "--language", dest = "lang", default = "en", help = "Language to load translations from")
args = parser.parse_args()

data = bytearray(args.file.read())

data = bin.patch.main(args.lang, data, "bin")
data = cmcd.patch.main(args.lang, data, "cmcd")
data = overlay.patch.main(args.lang, data, "overlay")

text = "eCDP English Translation Patch v1.0.0 - https://github.com/eCDP-English/translation"
tbytes = text.encode("SHIFT-JIS")
tlen = len(tbytes)
blen = len(data)
offset = 0
for b in tbytes:
	data[blen-tlen+offset] = b
	offset += 1

print("Patches done. writing to file.")
fname = args.file.name
open(fname[0:len(fname)-4] + "_patched.nds", "wb").write(data)