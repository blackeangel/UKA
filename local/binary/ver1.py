import sys
def FindStringInByteFile(word,file):
    findword =  bytes(word, 'utf-8')
    with open(file, "r+b") as f:
        for line in f:
            if findword in line:
               return line.__str__()[2:len(line.__str__())-3]

if __name__ == '__main__': 
	    print(FindStringInByteFile(sys.argv[1], sys.argv[2]))
