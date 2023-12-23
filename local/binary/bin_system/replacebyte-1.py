import mmap, sys, os
def replacebyte(file,whatfind,whatreplace):
      if whatreplace=='' or len(whatreplace)==0:
          for i in range(len(whatfind)):
              whatreplace=whatreplace+'0'
      if whatfind.isdigit() == True:
          whatfind=str(hex(int(whatfind)))[2:]
      if whatfind[:2]=='0x':
          whatfind=whatfind[2:]
      if (len(whatfind)/2).is_integer()==False:
          whatfind='0'+whatfind
      print("finding value in hex: "+whatfind)
      whatfindhex=whatfind
      if whatreplace.isdigit() == True:
          whatreplace=str(hex(int(whatreplace)))[2:]
      if whatreplace[:2] == '0x':
          whatreplace=whatreplace[2:]
      if (len(whatreplace)/2).is_integer()==False:
          whatreplace='0'+whatreplace
      print("replacing value in hex: "+whatreplace)
      whatreplacehex=whatreplace
      if len(whatfind)!=len(whatreplace):
          print("length whatfind != length whatreplace")
          return        
      whatfind=bytes.fromhex(whatfind)
      whatreplace=bytes.fromhex(whatreplace)
      with open(file, 'r+b') as f:
          step=len(whatfind)
          offset=0
          size = os.stat(file).st_size
          mm=mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
          k=0
          while True:
                if offset + step > size:
                      break
                pos = mm.find(whatfind, offset, offset + step)
                if pos == -1:
                      offset += step
                else:
                      k+=1
                      mm.seek(pos)
                      print("finding value in offset: "+str(hex(pos)))
                      mm.write(whatreplace)
                      print('replacing %s on %s in offset %s'%(str(whatfindhex), str(whatreplacehex), str(hex(pos))))
                      offset = pos + len(whatfind)
          if k==0:
              print('searching value not found!')
                      
if __name__ == '__main__':
    if sys.argv.__len__() == 4:
        replacebyte(sys.argv[1], sys.argv[2], sys.argv[3])