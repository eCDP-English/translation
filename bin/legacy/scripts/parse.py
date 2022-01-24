import os

listfiles=os.listdir("./original")

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

for filename in listfiles:
	print(filename)
	f=open("./original/"+filename,"rb")
	o=f.read()
	f.close()
	offsets=getMetaData(o)
	strings=[]
	for i in offsets:
		strings.append(getStringAtOffset(o,i))
	f=open("./txt/"+filename+".txt","w")
	f.write("\n===#===\n".join(strings))
	f.close()