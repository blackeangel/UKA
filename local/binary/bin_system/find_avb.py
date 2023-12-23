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
        offfset=mm.find(whatfind)
        if offfset>0:
            if size>read_dump:
                offfset=(size-read_dump)+offfset
            print(".....finding AVB structure in %s"%(hex(offfset)))
        else:
            print(".....AVB structure not found!")
    return offfset
    
def main(file, whatfind, savefolder):
    offset=reversefinder(file, whatfind)
    if offset>0:
        avbtxt=os.path.basename(os.path.abspath(file))
        #avb=re.sub('[[|.|+|(|-|_]',' ', avbtxt).split(' ')[0]
        avb=re.split('\[|\.|\+|\(|-|_| ', avbtxt, maxsplit=1)[0]
        fileavbtxt=savefolder + os.sep + avb + "_size_avb.txt"
        ftxt=open(fileavbtxt,'tw')
        print(offset,file=ftxt)
        ftxt.close()
        size=os.stat(file).st_size
        nwritebyte=size-offset
        with open(file,'rb') as f:
            f.seek(offset)
            readbyte=f.read(nwritebyte)
        fileavb=savefolder + os.sep + avb + "_avb.img"
        with open(fileavb,'wb') as favb:
            favb.write(readbyte)
    else:
        return
         
if __name__ == '__main__':
    if sys.argv.__len__() == 3:
        main(sys.argv[1], sys.argv[2],os.path.dirname(os.path.abspath(sys.argv[2])))
    if sys.argv.__len__() == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
