import sys
#Using: python3 path/to/file offset value
def writebyte(file,offset,value):
    fh = open(file, "rb+")
    fh.seek(int(offset,16))
    fh.write(bytes.fromhex(value))
    fh.close()

if __name__ == '__main__':
    if sys.argv.__len__() == 4:
        writebyte(sys.argv[1], sys.argv[2], sys.argv[3])
