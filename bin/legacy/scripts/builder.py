import os

listfiles=os.listdir("./txt")

def LEshort(num):
	lower=num%256
	higher=num//256
	return bytes([lower,higher])

for filename in listfiles:
	f=open("./txt/"+filename)
	o=f.read()
	f.close()
	strings=o.strip().split("\n===#===\n")
	stringBytes=[ i.encode(encoding="shift-jisx0213")+b"\x00" for i in strings]

	numStrings=len(strings)
	offset=2*(numStrings+1)

	t=b""
	t+=LEshort(numStrings)
	for i in stringBytes:
		t+=LEshort(offset)
		offset+=len(i)
	for i in stringBytes:
		t+=i

	f=open("./modified/"+filename[:-4],"wb")
	f.write(t)
	f.close()
