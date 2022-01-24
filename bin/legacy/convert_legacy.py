import os
import json

def LEshort(num):
	lower=num%256
	higher=num//256
	return bytes([lower,higher])

for folder in os.listdir("en"):
	for file in os.listdir("en/" + folder):
		print("en/" + folder + "/" + file)
		f=open("en/" + folder + "/" + file, encoding='UTF-8')
		o=f.read()
		f.close()
		strings=o.strip().split("\n===#===\n")
		jsonData = json.dumps(strings, indent=4, ensure_ascii=False)
		open("en_converted/" + folder + "/" + file[0:len(file)-8] + ".json", "wb").write(bytes(jsonData, "UTF-8"))
