#!/bin/python3

# Required: 

ROM_NAME = "ecdp"
IGNORE_MD5 = True

# Custom Rules Begin Here

# This script contains configuration for create.py and patch.py,
# This example one just excludes anything that is not a valid fullwidth shift-jis character -
# Feel free to change it however you want.

minimum_length = 3 #minimum length, in amount of bytes (not characters!)

range_ascii = [
	[0x0A, 0x0A], #newline (control char)

	#lets ignore these for now, we want full width strings
	#[0x30, 0x39], #numbers
	#[0x41, 0x5A], #uppercase alphabets
	#[0x61, 0x7A], #lowercase alphabets
]

range_sjis = [
	[0x824F, 0x8258], #numbers
	[0x8260, 0x8279], #uppercase alphabets
	[0x8281, 0x829A], #lowercase alphabets
	[0x829F, 0x82F1], #hiragana characters
	[0x8340, 0x8396], #katakana characters
	#kanjis
	[0x889F, 0x9872],
	[0x989F, 0x9FFC],
	[0xE040, 0xEAA4],
]

#always valid when a string starts with any of these
#(still goes through control character checks)
exceptions = [
	"SOC",
	"「",
	"DS"
]

#you probably don't want to edit this
control_chars = [
	[0x00, 0x09],
	[0x0B, 0x1F],
]

def check_valid(obytes):
	if len(obytes) < minimum_length:
		return False

	#check for control characters in the whole string
	i = 0
	while i < len(obytes):
		j = 0
		while j < len(control_chars):
			range = control_chars[j]
			if obytes[i] >= range[0] and obytes[i] <= range[1]:
				return False
			j += 1
		i += 1

	#exception checks
	str = obytes.decode("SHIFT-JIS")
	i = 0
	while i < len(exceptions):
		if (str.startswith(exceptions[i])):
			return True
		i += 1

	#doesn't need to check the whole string, garbage strings usually have invalid character at the start
	firstByte = obytes[0]
	secondByte = obytes[1]

	#check if it's a valid 1-byte character
	i = 0
	while i < len(range_ascii):
		range = range_ascii[i]

		if firstByte >= range[0] and firstByte <= range[1]:
			return True

		i += 1
	
	#check if it's a valid 2-byte character
	i = 0
	while i < len(range_sjis):
		range = range_sjis[i]
		byte = firstByte * 0x100 + secondByte

		if byte >= range[0] and byte <= range[1]:
			return True
		
		i += 1

	return False

