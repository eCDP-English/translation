#!/bin/python3
import bin.patch
import arm9.patch
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
data = arm9.patch.main(args.lang, data, "arm9")

text = "eCDP English Translation Patch v1.1.2 - https://github.com/eCDP-English/translation"
for b in text.encode("SHIFT-JIS"):
	data.append(b)

print("Patches done. writing to file.")
fname = args.file.name
open(fname[0:len(fname)-4] + "_patched.nds", "wb").write(data)
