import sys, os
def finder(file, whatfind):
    whatfind=bytes.fromhex(whatfind)
    size=os.stat(file).st_size
    read_dump=size
    with open(file, "rb") as f:
        f.seek(size-read_dump)
        mm=f.read(read_dump)
        offfset=mm.find(whatfind)
        if offfset>=0:
            offfset=(size-read_dump)+offfset
            #print(".....finding  header .gz in %s"%(hex(offfset)))
    return offfset
    
def main(file, whatfind, savefolder):
    offset=finder(file, whatfind)
    if offset>=0:
        #fileavbtxt="kernel.txt"
        #ftxt=open(fileavbtxt,'tw')
        #print(offset,file=ftxt)
        #ftxt.close()
        size=os.stat(file).st_size
        nwritebyte=size-offset
        with open(file,'rb') as f:
            f.seek(offset)
            readbyte=f.read(nwritebyte)
        fileavb="kernel.gz"
        with open(fileavb,'wb') as favb:
            favb.write(readbyte)
    else:
        return
         
if __name__ == '__main__':
    if sys.argv.__len__() == 3:
        main(sys.argv[1], sys.argv[2],os.path.dirname(os.path.abspath(sys.argv[2])))
    if sys.argv.__len__() == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
