import mmap, sys, os
def FindStringInByteFile(word,file):
    findword =  bytes(word, 'utf-8')
    detctbuild = bytes("begin build properties", 'utf-8')
    with open(file, "r+b") as f:
            step = mmap.ALLOCATIONGRANULARITY
            offset = 0
            size = os.stat(file).st_size
            map_ = mmap.mmap(f.fileno(), length=step)
            while True:
                    offset += step
                    if offset + step > size:
                        break
                    if map_.find(detctbuild)==-1:
                        map_ = mmap.mmap(f.fileno(), length=step, offset=offset)
                    else:
                        offset=map_.find(detctbuild)
                        break
            while True:
                offset += step
                if offset + step > size:
                    break
                if map_.find(findword) == -1:
                    map_ = mmap.mmap(f.fileno(), length=step, offset=offset)
                else:
                    map_.seek(map_.find(findword))
                    line=map_.read(50).__str__()
                    rez=line[2:len(line)-1].split('\\n')[0]
                    #return rez # возвращает всю строку
                    return rez.split('=')[1] # будет возвращать только то что после равно
            map_.close()
if __name__ == '__main__':
    print(FindStringInByteFile(sys.argv[1], sys.argv[2]))