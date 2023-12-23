import sys, os, re, mmap
def reversefinder(file, whatfind):
    whatfind=bytes.fromhex(whatfind)
    size=os.stat(file).st_size
    read_dump=128000000
    with open(file, "rb") as f:
        if size>read_dump:
            f.seek(size-read_dump)
            mm=f.read(read_dump)
        else:
            mm=mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        offfset=mm.rfind(whatfind)
        if offfset>=0:
            if size>read_dump:
                offfset=(size-read_dump)+offfset
            #print(".....finding AVB structure in %s"%(hex(offfset)))
            print(offfset)
    return
        #else:
            #print(".....AVB structure not found!")
    #return
    
if __name__ == '__main__':
    if sys.argv.__len__() == 3:
        print(reversefinder(sys.argv[1], sys.argv[2]))