import os
import sys
import struct
import traceback
import shutil
import re
import mmap
import tarfile
import time
import ext4
import string
import argparse
'''
authors:
https://github.com/unix3dgforce
https://github.com/blackeangel
'''
EXT4_HEADER_MAGIC = 0xED26FF3A
EXT4_SPARSE_HEADER_LEN = 28
EXT4_CHUNK_HEADER_SIZE = 12


class ext4_file_header(object):
    def __init__(self, buf):
        (self.magic,
         self.major,
         self.minor,
         self.file_header_size,
         self.chunk_header_size,
         self.block_size,
         self.total_blocks,
         self.total_chunks,
         self.crc32) = struct.unpack('<I4H4I', buf)


class ext4_chunk_header(object):
    def __init__(self, buf):
        (self.type,
         self.reserved,
         self.chunk_size,
         self.total_size) = struct.unpack('<2H2I', buf)


class Extractor(object):
    def __init__(self):
        self.FileName = ""
        self.BASE_DIR = ""
        self.OUTPUT_IMAGE_FILE = ""
        self.EXTRACT_DIR = ""
        self.BLOCK_SIZE = 4096
        self.TYPE_IMG = 'system'
        self.context = []
        self.fsconfig = []
        self.isSAR = False
        # 07.05.23 -->
        self.Listing = False
        self.ggdtxt = []
        self.ggftxt = []
        self.linkmass = [] # link for autoftxt 20.10.2023
        self.avtoftxt = []
        self.ftxt = []
        self.fsconfig_e2fsdroid = [] # fs_config list fo fs_config file to e2fsdroid 20.10.2023
        # <-- 07.05.23

    def __remove(self, path):
        if os.path.isfile(path):
            os.remove(path)  # remove the file
        elif os.path.isdir(path):
            shutil.rmtree(path)  # remove dir and all contains
        else:
            raise ValueError("file {} is not a file or dir.".format(path))

    def __logtb(self, ex, ex_traceback=None):
        if ex_traceback is None:
            ex_traceback = ex.__traceback__
        tb_lines = [line.rstrip('\n') for line in
                    traceback.format_exception(ex.__class__, ex, ex_traceback)]
        return '\n'.join(tb_lines)

    def __file_name(self, file_path):
        name = os.path.basename(file_path).rsplit('.', 1)[0]
        return name

    def __appendf(self, msg, log_file):
        if not os.path.isfile(log_file):
            open(log_file, 'tw', encoding='utf-8').close()
        with open(log_file, 'a', newline='\n') as file:
            print(msg, file=file)

    # 08.05.2023 -->
    def __createtar_symlink(self, path_tarfile, name, uid, gid, mode, link):
        #if not os.path.exists(path_tarfile):
        #    fd = tarfile.open(path_tarfile, 'x')
        #    fd.close()
        obj = tarfile.TarInfo('Test')
        obj.name = name
        obj.uid = uid  # 0o2000
        obj.gid = gid  # 0o1000
        obj.mode = mode  # 0o644
        obj.uname = str(obj.uid)
        obj.gname = str(obj.gid)
        obj.mtime = time.time()
        obj.type = tarfile.SYMTYPE
        obj.linkpath = link
        fd = tarfile.open(path_tarfile, 'a')
        fd.addfile(obj)
        fd.close()

    # <-- 08.05.2023

    def __getperm(self, arg):
        if len(arg) < 9 or len(arg) > 10:
            return
        if len(arg) > 8:
            arg = arg[1:]
        oor, ow, ox, gr, gw, gx, wr, ww, wx = list(arg)
        o, g, w, s = 0, 0, 0, 0
        if oor == 'r': o += 4
        if ow == 'w': o += 2
        if ox == 'x': o += 1
        if ox == 'S': s += 4
        if ox == 's': s += 4; o += 1
        if gr == 'r': g += 4
        if gw == 'w': g += 2
        if gx == 'x': g += 1
        if gx == 'S': s += 2
        if gx == 's': s += 2; g += 1
        if wr == 'r': w += 4
        if ww == 'w': w += 2
        if wx == 'x': w += 1
        if wx == 'T': s += 1
        if wx == 't': s += 1; w += 1
        return str(s) + str(o) + str(g) + str(w)

    def __ImgSizeFromSparseFile(self, target):
        with open(target, "rb") as img_file:
            if self.sign_offset > 0:
                img_file.seek(self.sign_offset, 0)
            header = ext4_file_header(img_file.read(28))
            imgsize=header.block_size*header.total_blocks
        return imgsize

    def __ImgSizeFromRawFile(self, target):
        with open(target, "rb") as img_file:
            m = ''
            see = 0x404
            for i in reversed(range(0, 4)):
                img_file.seek(see + i, 0)
                m = m + img_file.read(1).hex()
                imgsize = int('0x' + m, 0) * 4096
        return imgsize

    def __ext4extractor(self):
        # 25.04.2021 -->
        config_dir = os.path.dirname(self.EXTRACT_DIR) + os.sep + 'config' + os.sep + self.FileName + os.sep
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)
        # 07.05.23 -->
        avto_f_txt = config_dir + self.FileName + "_avto_f.txt"
        f_txt = config_dir + self.FileName + "_f.txt"
        gg_d_txt = config_dir + self.FileName + "_gg_d.txt"
        gg_f_txt = config_dir + self.FileName + "_gg_f.txt"
        pack_avb_sh = config_dir + self.FileName + "_pack_avb.sh"
        pack_avb_sparse_sh = config_dir + self.FileName + "_pack_avb_sparse.sh"
        # <-- 07.05.23
        fs_config_file = config_dir + self.FileName + "_fs_config"
        fs_config_file_e2fsdroid = config_dir + self.FileName + "_fs_config_e2fsdroid"
        contexts = config_dir + self.FileName + "_file_contexts"
        pack_sh = config_dir + self.FileName + "_pack.sh"
        pack_sparse_sh = config_dir + self.FileName + "_pack_sparse.sh"
        size = config_dir + self.FileName + "_size.txt"
        name = config_dir + self.FileName + "_name.txt"
        spaces_file = config_dir + self.FileName + "_space.txt"
        part_name = config_dir + self.FileName + "_part_name.txt"
        self.__appendf('make_ext4fs -J -T -1 -S ./file_contexts -C ./fs_config -l ' + str(os.path.getsize(self.OUTPUT_IMAGE_FILE)) + ' -a /' + self.FileName + ' "$outdir"/' + self.FileName + '.new.img ' + self.FileName + '', pack_sh)
        self.__appendf('make_ext4fs -s -J -T -1 -S ./file_contexts -C ./fs_config -l ' + str(os.path.getsize(self.OUTPUT_IMAGE_FILE)) + ' -a /' + self.FileName + ' "$outdir"/' + self.FileName + '.new.img ' + self.FileName + '', pack_sparse_sh)
        self.__appendf(os.path.getsize(self.OUTPUT_IMAGE_FILE), size)
        self.__appendf(os.path.basename(self.OUTPUT_IMAGE_FILE).rsplit('.', 1)[0], name)
        # 07.05.23 -->
        self.__appendf('make_ext4fs -J -T -1 -S ./file_contexts -C ./fs_config -l "$size_avb" -a /"$pack_d" "$outdir"/"$pack_d".new.img $pack_d', pack_avb_sh)
        self.__appendf('make_ext4fs -s -J -T -1 -S ./file_contexts -C ./fs_config -l "$size_avb" -a /"$pack_d" "$outdir"/"$pack_d".new.img $pack_d', pack_avb_sparse_sh)
        # <-- 07.05.23
        # 08.05.2023 -->
        tar_file_symlink = config_dir + self.FileName + "_sim.tar"
        # <-- 08.05.2023
        # <-- 25.04.2021
        fuking_symbols = '\\^$.|?*+(){}[]'

        def scan_dir(root_inode, root_path=""):
            for entry_name, entry_inode_idx, entry_type in root_inode.open_dir():
                if entry_name in ['.', '..'] or entry_name.endswith(' (2)'):
                    continue
                entry_inode = root_inode.volume.get_inode(entry_inode_idx, entry_type)
                entry_inode_path = root_path + '/' + entry_name
                mode = self.__getperm(entry_inode.mode_str)
                uid = entry_inode.inode.i_uid
                gid = entry_inode.inode.i_gid
                con = ''
                cap = ''
                for i in list(entry_inode.xattrs()):
                    if i[0] == 'security.selinux':
                        con = i[1].decode('utf8')[:-1]
                    elif i[0] == 'security.capability':
                        raw_cap = struct.unpack("<5I", i[1])
                        if raw_cap[1] > 65535:
                            cap = '' + str(hex(int('%04x%04x' % (raw_cap[3], raw_cap[1]), 16)))
                        else:
                            cap = '' + str(hex(int('%04x%04x%04x' % (raw_cap[3], raw_cap[2], raw_cap[1]), 16)))
                        cap = ' capabilities={cap}'.format(cap=cap)
                if entry_inode.is_dir:
                    dir_target = self.EXTRACT_DIR + entry_inode_path.replace(' ', '_')

                    if not self.Listing:
                        if not os.path.isdir(dir_target):
                            os.makedirs(dir_target)
                        if os.name == 'posix':
                            os.chmod(dir_target, int(mode, 8))
                            os.chown(dir_target, uid, gid)

                    scan_dir(entry_inode, entry_inode_path)
                    # 07.05.23 -->
                    tmppath = self.FileName + entry_inode_path
                    if tmppath.find(' ', 1, len(tmppath)) > 0:
                        self.__appendf(tmppath, spaces_file)
                        tmppath = tmppath.replace(' ', '_')
                    self.ggdtxt.append('%s %s %s %s' % (tmppath, uid, gid, mode))
                    # <-- 07.05.23
                    if cap == '' and con == '':
                       self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode))
                    else:
                        if cap == '':
                            self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode))
                            for fuk_symb in fuking_symbols:
                                tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                            self.context.append('/%s %s' % (tmppath + "(/.*)?", con))
                            self.context.append('/%s %s' % (tmppath, con))
                        else:
                            if con == '':
                                self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode + cap))
                            else:
                                self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode + cap))
                                for fuk_symb in fuking_symbols:
                                    tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                                self.context.append('/%s %s' % (tmppath + "(/.*)?", con))
                                self.context.append('/%s %s' % (tmppath, con))
                elif entry_inode.is_file:
                    try:
                        raw = entry_inode.open_read().read()
                    except:
                        continue
                    wdone = None
                    file_target = self.EXTRACT_DIR + entry_inode_path.replace('/', os.sep).replace(' ', '_')
                    # 07.05.23 -->
                    if entry_name == "plat_file_contexts":
                        with open(contexts + "_orig", 'wb') as out:
                            out.write(raw)
                    # <-- 07.05.23
                    if not self.Listing:
                        if os.name == 'nt':
                            if entry_name.endswith('/'):
                                entry_name = entry_name[:-1]
                            file_target = self.EXTRACT_DIR + entry_inode_path.replace('/', os.sep).replace(' ', '_')
                            if not os.path.isdir(os.path.dirname(file_target)):
                                os.makedirs(os.path.dirname(file_target))
                            with open(file_target, 'wb') as out:
                                out.write(raw)
                        if os.name == 'posix':
                            file_target = self.EXTRACT_DIR + entry_inode_path.replace(' ', '_')
                            if not os.path.isdir(os.path.dirname(file_target)):
                                os.makedirs(os.path.dirname(file_target))
                            with open(file_target, 'wb') as out:
                                out.write(raw)
                            os.chmod(file_target, int(mode, 8))
                            os.chown(file_target, uid, gid)

                    tmppath = self.FileName + entry_inode_path
                    if tmppath.find(' ', 1, len(tmppath)) > 0:
                        self.__appendf(tmppath, spaces_file)
                        tmppath = tmppath.replace(' ', '_')
                    self.ggftxt.append('%s %s %s %s' % (tmppath, uid, gid, mode))

                    if cap == '' and con == '':
                        self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode))
                    else:
                        if cap == '':
                            self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode))
                            for fuk_symb in fuking_symbols:
                                tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                            self.context.append('/%s %s' % (tmppath, con))
                        else:
                            if con == '':
                                self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode + cap))
                            else:
                                self.fsconfig.append('%s %s %s %s' % (tmppath, uid, gid, mode + cap))
                                for fuk_symb in fuking_symbols:
                                    tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                                self.context.append('/%s %s' % (tmppath, con))
                elif entry_inode.is_symlink:
                    # try:
                    link_target = entry_inode.open_read().read().decode("utf8")
                    target = self.EXTRACT_DIR + entry_inode_path.replace(' ', '_')
                    tmppath = self.FileName + entry_inode_path
                    if tmppath.find(' ', 1, len(tmppath)) > 0:
                        self.__appendf(tmppath, spaces_file)
                        tmppath = tmppath.replace(' ', '_')
                    # 08.05.2023 -->
                    self.__createtar_symlink(tar_file_symlink, tmppath, uid, gid, int(mode), link_target)
                    # <-- 08.05.2023
                    # 20.10.2023 -->
                    self.linkmass.append('%s -> %s %s %s %s' % (tmppath, link_target, uid, gid, mode))
                    self.fsconfig_e2fsdroid.append('%s %s %s %s' % (tmppath, uid, gid, mode))
                    # <-- 20.10.2023
                    try:
                        if cap == '' and con == '':
                            self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode, link_target))
                        else:
                            if cap == '':
                                self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode, link_target))
                                for fuk_symb in fuking_symbols:
                                    tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                                self.context.append('/%s %s' % (tmppath, con))
                            else:
                                if con == '':
                                    self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode + cap, link_target))
                                else:
                                    self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode + cap, link_target))
                                    for fuk_symb in fuking_symbols:
                                        tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                                    self.context.append('/%s %s' % (tmppath, con))
                        if os.path.islink(target):
                            try:
                                os.remove(target)
                            except:
                                pass
                        if os.path.isfile(target):
                            try:
                                os.remove(target)
                            except:
                                pass
                        if not self.Listing:
                            if os.name == 'posix':
                                os.symlink(link_target, target)
                            if os.name == 'nt':
                                with open(target.replace('/', os.sep), 'wb') as out:
                                    tmp = bytes.fromhex('213C73796D6C696E6B3EFFFE')
                                    for index in list(link_target):
                                        tmp += struct.pack('>sx', index.encode('utf-8'))
                                    out.write(tmp + struct.pack('xx'))
                                    os.system('attrib +s "%s"' % target.replace('/', os.sep))
                        if not all(c in string.printable for c in link_target):
                            pass
                        if entry_inode_path[1:] == entry_name or link_target[1:] == entry_name:
                            self.symlinks.append('%s %s' % (link_target, entry_inode_path[1:]))
                        else:
                            self.symlinks.append('%s %s' % (link_target, self.FileName + entry_inode_path))
                    except:
                        try:
                            link_target_block = int.from_bytes(entry_inode.open_read().read(), "little")
                            link_target = root_inode.volume.read(link_target_block * root_inode.volume.block_size, entry_inode.inode.i_size).decode("utf8")
                            target = self.EXTRACT_DIR + entry_inode_path.replace(' ', '_')
                            tmppath = self.FileName + entry_inode_path
                            if tmppath.find(' ', 1, len(tmppath)) > 0:
                                self.__appendf(tmppath, spaces_file)
                                tmppath = tmppath.replace(' ', '_')
                            if link_target and all(c in string.printable for c in link_target):
                                if cap == '' and con == '':
                                    self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode, link_target))
                                else:
                                    if cap == '':
                                        self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode, link_target))
                                        for fuk_symb in fuking_symbols:
                                            tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                                        self.context.append('/%s %s' % (tmppath, con))
                                    else:
                                        if con == '':
                                            self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode + cap, link_target))
                                        else:
                                            self.fsconfig.append('%s %s %s %s %s' % (tmppath, uid, gid, mode + cap, link_target))
                                            for fuk_symb in fuking_symbols:
                                                tmppath = tmppath.replace(fuk_symb, '\\' + fuk_symb)
                                            self.context.append('/%s %s' % (tmppath, con))
                                if not self.Listing:
                                    if os.name == 'posix':
                                        os.symlink(link_target, target)
                                    if os.name == 'nt':
                                        with open(target.replace('/', os.sep), 'wb') as out:
                                            tmp = bytes.fromhex('213C73796D6C696E6B3EFFFE')
                                            for index in list(link_target):
                                                tmp += struct.pack('>sx', index.encode('utf-8'))
                                            out.write(tmp + struct.pack('xx'))
                                            os.system('attrib +s %s' % target.replace('/', os.sep))
                            else:
                                pass
                        except:
                            pass

        with open(self.OUTPUT_IMAGE_FILE, 'rb') as file:
            root = ext4.Volume(file).root
            # 06.10.2023 -->
            uuid = config_dir + self.FileName + "_uuid.txt"
            self.__appendf(ext4.Volume(file).uuid, uuid)
            timefile = config_dir + self.FileName + "_time.txt"
            time=ext4.Volume(file).mkfs_time
            if time == 0:
                lastcheck = ext4.Volume(file).lastcheck()
                checkinterval = ext4.Volume(file).checkinterval()
                if checkinterval > 1:
                    time = lastcheck/checkinterval
                else:
                    time = lastcheck
                time = min(time, ext4.Volume(file).mtime(), ext4.Volume(file).wtime())
            self.__appendf(time,timefile)
            # 06.10.2023 <--

            # 20.10.2023 -->
            rootdirperm = self.__getperm(ext4.Volume(file).root.mode_str.__str__())
            rootdiruid = ext4.Volume(file).root.inode.i_uid
            rootdirgid = ext4.Volume(file).root.inode.i_gid
            for i in list(ext4.Volume(file).root.xattrs()):
                if i[0] == 'security.selinux':
                    rootdircon = i[1].decode('utf8')[:-1]
            #self.fsconfig.append('%s %s %s %s' % ("/", rootdiruid, rootdirgid, rootdirperm))
            self.fsconfig_e2fsdroid.append('%s %s %s %s' % ("/", rootdiruid, rootdirgid, rootdirperm))
            #self.context.append('/%s %s' % ("/", rootdircon))

            pname = ext4.Volume(file).volume_name()
            if pname == '':
                pname = ext4.Volume(file).last_mounted().replace('/','')
            self.__appendf(pname, part_name)
            # 20.10.2023 <--
            dirlist = []
            for file_name, inode_idx, file_type in root.open_dir():
                dirlist.append(file_name)
            dirr = re.sub('(\.)', '\\.', self.FileName)
            setattr(self, 'DIR', dirr)
            scan_dir(root)
            self.fsconfig.sort()
            self.__appendf('\n'.join(self.fsconfig), fs_config_file)  # 2021/04/25
            if self.context:  # 11.05.18
                self.context.sort()  # 11.05.18

                if self.isSAR:
                    self.context.insert(0, '/' + dirr + '/' + ' u:object_r:rootfs:s0')
                    self.context.insert(1, '/' + dirr + '(/.*)? u:object_r:rootfs:s0')
                if not self.isSAR:
                    for c in self.context:
                        if re.search('^/' + dirr + '/build..prop ', c):
                            self.context.insert(0, '/' + dirr + '(/.*)? ' + c.split(" ")[1])
                            break
                        else:
                            if re.search('lost..found', c):
                                self.context.insert(0, '/' + dirr + '(/.*)? ' + c.split(" ")[1])
                                break
                self.__appendf('\n'.join(self.context), contexts)  # 11.05.18

                # 07.05.23 -->
                self.ggftxt.sort()
                self.__appendf('\n'.join(self.ggftxt), gg_f_txt) # закоментируй если считаешь, что работает не так, либо давай обсудим и допилим
                self.ggdtxt.sort()
                self.__appendf('\n'.join(self.ggdtxt), gg_d_txt) # закоментируй если считаешь, что работает не так, либо давай обсудим и допилим
                for m in self.ggdtxt:
                    self.avtoftxt.append(m + " _d")
                    self.fsconfig_e2fsdroid.append(m)
                for n in self.ggftxt:
                    self.avtoftxt.append(n + " _f")
                    self.fsconfig_e2fsdroid.append(n)
                for k in self.linkmass:
                    self.avtoftxt.append(k + " _l")
                self.avtoftxt.insert(0, dirr + ' 0 0 0755 _d')
                self.__appendf('\n'.join(self.avtoftxt), avto_f_txt) # закоментируй если считаешь, что работает не так, либо давай обсудим и допилим
                self.fsconfig_e2fsdroid.sort()
                self.__appendf('\n'.join(self.fsconfig_e2fsdroid), fs_config_file_e2fsdroid) # 20.10.2023
                for l in self.avtoftxt:
                    tmp=re.sub(' ->.* \d{1,4} \d{1,4} \d{1,4} ', "", l) # 20.10.2023
                    tmp=re.sub(' \d{1,4} \d{1,4} \d{1,4} ', "", tmp) # 20.10.2023
                    self.ftxt.append(tmp)
                self.__appendf('\n'.join(self.ftxt), f_txt) # закоментируй если считаешь, что работает не так, либо давай обсудим и допилим
                if os.path.isfile(contexts + "_orig"):
                    lines = []
                    with open(contexts + "_orig") as file:
                        lines = file.readlines()
                    for i in range(len(lines)):
                        lines[i] = "/" + dirr + lines[i].strip()
                    file1 = open(contexts + "_orig", "w")
                    file1.close()
                    self.__appendf('\n'.join(lines), contexts + "_orig")
                # 07.05.23 <--

    def __converSimgToImg(self, target):
        with open(target, "rb") as img_file:
            if self.sign_offset > 0:
                img_file.seek(self.sign_offset, 0)
            header = ext4_file_header(img_file.read(28))
            total_chunks = header.total_chunks
            if header.file_header_size > EXT4_SPARSE_HEADER_LEN:
                img_file.seek(header.file_header_size - EXT4_SPARSE_HEADER_LEN, 1)
            with open(target.rsplit('.', 1)[0] + ".raw.img", "wb") as raw_img_file:
                sector_base = 82528
                output_len = 0
                while total_chunks > 0:
                    chunk_header = ext4_chunk_header(img_file.read(EXT4_CHUNK_HEADER_SIZE))
                    sector_size = (chunk_header.chunk_size * header.block_size) >> 9
                    chunk_data_size = chunk_header.total_size - header.chunk_header_size
                    if chunk_header.type == 0xCAC1:  # CHUNK_TYPE_RAW
                        if header.chunk_header_size > EXT4_CHUNK_HEADER_SIZE:
                            img_file.seek(header.chunk_header_size - EXT4_CHUNK_HEADER_SIZE, 1)
                        data = img_file.read(chunk_data_size)
                        len_data = len(data)
                        if len_data == (sector_size << 9):
                            raw_img_file.write(data)
                            output_len += len_data
                            sector_base += sector_size
                    else:
                        if chunk_header.type == 0xCAC2:  # CHUNK_TYPE_FILL
                            if header.chunk_header_size > EXT4_CHUNK_HEADER_SIZE:
                                img_file.seek(header.chunk_header_size - EXT4_CHUNK_HEADER_SIZE, 1)
                            data = img_file.read(chunk_data_size)
                            len_data = sector_size << 9
                            raw_img_file.write(struct.pack("B", 0) * len_data)
                            output_len += len(data)
                            sector_base += sector_size
                        else:
                            if chunk_header.type == 0xCAC3:  # CHUNK_TYPE_DONT_CARE
                                if header.chunk_header_size > EXT4_CHUNK_HEADER_SIZE:
                                    img_file.seek(header.chunk_header_size - EXT4_CHUNK_HEADER_SIZE, 1)
                                data = img_file.read(chunk_data_size)
                                len_data = sector_size << 9
                                raw_img_file.write(struct.pack("B", 0) * len_data)
                                output_len += len(data)
                                sector_base += sector_size
                            else:
                                len_data = sector_size << 9
                                raw_img_file.write(struct.pack("B", 0) * len_data)
                                sector_base += sector_size
                    total_chunks -= 1
        self.OUTPUT_IMAGE_FILE = target.rsplit('.', 1)[0] + ".raw.img"

    def fixmoto(self, input_file):
        if not os.path.exists(input_file):
            return
        output_file = input_file + "_"
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                pass
        with open(input_file, 'rb') as f:
            data = f.read(500000)
        moto = re.search(b'\x4d\x4f\x54\x4f', data)
        if not moto:
            return
        result = []
        for i in re.finditer(b'\x53\xEF', data):
            result.append(i.start() - 1080)
        offset = 0
        for i in result:
            if data[i] == 0:
                offset = i
                break
        if offset > 0:
            with open(output_file, 'wb') as o, open(input_file, 'rb') as f:
                data = f.seek(offset)
                data = f.read(15360)
                while data:
                    devnull = o.write(data)
                    data = f.read(15360)
        try:
            os.remove(input_file)
            os.rename(output_file, input_file)
        except:
            pass

    def checkSignOffset(self, file):
        size = os.stat(file.name).st_size
        if size <= 1048576:
            mm = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        else:
            mm = mmap.mmap(file.fileno(), 1048576, access=mmap.ACCESS_READ)  # 1048576=1Mb
        offset = mm.find(struct.pack('<L', EXT4_HEADER_MAGIC))
        return offset

    def __getTypeTarget(self, target):
        with open(target, "rb") as img_file:
            setattr(self, 'sign_offset', self.checkSignOffset(img_file))
            if self.sign_offset > 0:
                img_file.seek(self.sign_offset, 0)
            header = ext4_file_header(img_file.read(28))
            if header.magic != EXT4_HEADER_MAGIC:
                print(".....Detected raw image.....")
                return 'img'
            else:
                print(".....Detected sparse image.....")
                return 'simg'

    def ___sar_detect(self, img_file):
        import ext4, string, struct
        with open(img_file, 'rb') as file:
            root = ext4.Volume(file).root
            for entry_name, entry_inode_idx, entry_type in root.open_dir():
                if entry_name in ['.', '..'] or entry_name.endswith(' (2)'):
                    continue
                entry_inode = root.volume.get_inode(entry_inode_idx, entry_type)
                if entry_inode.is_symlink and (entry_name == "init" or entry_name == "d"):
                    self.isSAR = True
        if self.isSAR == True:
            print(".....Detected image \"System as Root\"")
        else:
            print(".....Detected image not \"System as Root\"")

    def main(self, target, output_dir, list):
        if list:
            self.Listing = True
        self.BASE_DIR = (os.path.realpath(os.path.dirname(target)) + os.sep)
        self.BASE_MYDIR = (sys.argv[2]) + os.sep
        self.EXTRACT_DIR = os.path.realpath(os.path.dirname(output_dir)) + os.sep + self.__file_name(
            os.path.basename(output_dir))  # output_dir
        self.OUTPUT_IMAGE_FILE = self.BASE_DIR + os.path.basename(target)
        self.OUTPUT_MYIMAGE_FILE = os.path.basename(target)
        self.MYFileName = os.path.basename(self.OUTPUT_IMAGE_FILE).rsplit('.', 1)[0] + ".raw.img"
        self.FileName = self.__file_name(os.path.basename(target))
        target_type = self.__getTypeTarget(target)
        if target_type == 'simg':
            print(".....Convert %s to %s" % (
                os.path.basename(target), os.path.basename(target).rsplit('.', 1)[0] + ".raw.img"))
            self.__converSimgToImg(target)
        with open(os.path.abspath(self.OUTPUT_IMAGE_FILE), 'rb') as f:
            data = f.read(500000)
        moto = re.search(b'\x4d\x4f\x54\x4f', data)
        if moto:
            print(".....Finding MOTO structure! Fixing.....")
            self.fixmoto(os.path.abspath(self.OUTPUT_IMAGE_FILE))
        self.___sar_detect(os.path.abspath(self.OUTPUT_IMAGE_FILE))  # sar 09.02.2023
        print(".....Extraction from %s to %s" % (os.path.basename(target), os.path.basename(self.EXTRACT_DIR)))
        self.__ext4extractor()
        print(".....Done! All extraction in %s" % (os.path.basename(self.EXTRACT_DIR)))

def createParser ():
    parser = argparse.ArgumentParser(description='\n-------------------\nImgExtractor v 1.0b\n-------------------\nAuthors:\nunix3dgforce\nblackeangel\n')
    parser.add_argument('-i', '--image', help='input image, required argument')
    parser.add_argument('-o', '--outdir', help='output directory (current directory by default)')
    parser.add_argument('-L', '--list', help='Creating the "config" folder with configuration files without unpacking the image')
    return parser

if __name__ == '__main__':
    if os.name == 'nt':
        os.system('cls')
    if os.name == 'posix':
        os.system('clear')

    parser = createParser()
    args = parser.parse_args()
    if (args.image and args.image.__str__().strip() != ''):
        INPUT_IMAGE = args.image
    else:
        parser.print_help()
        sys.exit(2)

    if args.outdir:
        OUTDIR = args.outdir + os.sep + os.path.basename(INPUT_IMAGE)
    else:
        OUTDIR = os.path.realpath(os.path.dirname(INPUT_IMAGE)) + os.sep + os.path.basename(INPUT_IMAGE)

    if args.list:
        LIST = args.list
    else:
        LIST = False

    Extractor().main(INPUT_IMAGE, OUTDIR, LIST)

