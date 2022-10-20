import sys, os
def finder(file, whatfind):
    whatfind=bytes.fromhex(whatfind)
    size=os.stat(file).st_size
    read_dump=64000000
    with open(file, "rb") as f:
        if size>read_dump:
            mm=f.read(read_dump)
        else:
            mm=f.read()
        offfset=mm.find(whatfind)
        if offfset>=0:
           return (offfset)

if __name__ == '__main__':
    if sys.argv.__len__() == 3:
        print(finder(sys.argv[1], sys.argv[2]))


