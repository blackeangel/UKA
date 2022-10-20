#! /usr/bin/env python
#
# Copyright 2021 Alexander Kravchenko
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import io
import mmap
import os
import platform
import struct
import subprocess
import sys
import zlib
from shutil import which

if windows := os.name == 'nt':
    import winreg

help_message = f"""Usage: {sys.argv[0]} <kernel>

Description:
    Makes 32bit SAR kernels boot ramdisk.
    Refer to README.md for additional instructions."""


def main():
    #ver = platform.python_version()
    #ver = tuple(map(int, (ver.split("."))))
    #min_ver = tuple(map(int, ("3.9.0".split("."))))
    #if ver < min_ver:
        #sys.exit("ERROR: Python version too old. at least 3.9.0")
    if len(sys.argv) == 1:
        sys.exit(help_message)
    if sys.argv[1] in ['-h', '--help']:
        sys.exit(help_message)
    in_fn = sys.argv[1]
    # Check given file
    if os.path.exists(in_fn):
        in_fn = os.path.abspath(in_fn)
    else:
        raise Exception('File not found')
    BootWork(in_fn)


def printi(text):
    print(f"INFO: {text}")

def find_7z():
    if not windows:
        return '7zz' if which('7zz') != None else '7z'
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "Software\\7-Zip")
    path =  winreg.QueryValueEx(key, "Path")[0] + "7z.exe"
    printi(f"Found 7-Zip at: {path}")
    return path
    
sz = find_7z()


class BootWork:
    def __init__(self, filename):
        with open(filename, 'r+b') as f:
            header = struct.Struct('8s I I I I I I I I I 4x 16s 512s 8x')
            magic, kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size, second_addr, \
                tags_addr, page_size, dt_size, name, cmdline = header.unpack(f.read(header.size))

            if magic != b'ANDROID!':
                raise Exception(f"{filename} is not a valid android boot image\n")

            if kernel_size > 0:
                zimg_fobj = self.dump_part(f, page_size, kernel_size)
            p = Patch(zimg_fobj)
            new_kernel_data = p.new_zimg_data
            self.replace_part(new_kernel_data, f, page_size)

    def replace_part(self, data, file, offset):
        file.seek(offset, 0)
        file.write(data)

    def dump_part(self, f_in, offset, size):
        fobj = io.BytesIO()
        f_in.seek(offset, 0)
        fobj.write(f_in.read(size))
        return fobj

# ------------------------------------------------------
# Patch: Takes in a filepath to original zImage, returns modified.

class Patch:
    def __init__(self, zimg_file):
        self.zimg_file = zimg_file
        self.split_zimg(zimg_file)
        self.new_zimg_data = self.join_zimg()
        if self.zimg_len != len(self.new_zimg_data):
            error_msg = "Your kernel is probably corrupted or been tampered with \
                     If you have a rare device, or getting this after you check \
                     everything, create an issue on github."
            raise Exception(f"ERROR: Size mismatch!\n{error_msg}")


# split_zimg(filepath):
#   Takes a path to original zImage, splits it in parts
#   checking for inconsistancies in progress. Only the gzipped kernel is being modified afterwards
#   everything else is reused.

    def split_zimg(self, zimg_file):
        zimg_file.seek(0x24)
        data = struct.unpack("III", zimg_file.read(4 * 3))
        if data[0] != 0x016f2818:
            raise Exception(
                "ERROR: Didn't find IMG magic number")
        zimg_size = data[2]
        zimg_file.seek(0)
        d = zimg_file.read()
        self.gz_begin = d.find(b'\x1F\x8B\x08\x00')
        zimg_file.seek(0)
        self.unp_data = zimg_file.read(self.gz_begin)
        zimg_file.seek(self.gz_begin)
        gz_data = zimg_file.read()
        self.kernel_work(gz_data)
        gz_end = d.rfind(self.kernel_sz)
        self.gz_end = gz_end + 4
        self.gz_size = self.gz_end - self.gz_begin
        zimg_file.seek(self.gz_end)
        self.zimg_footer = zimg_file.read()
        self.pos = d.find(struct.pack("I", self.gz_end - 4))
        if (self.pos < 0x24 or self.pos > 0x400 or self.pos > self.gz_begin):
            raise Exception(
                "ERROR: Can't find offset of orig GZIP size field")
        zimg_file.close()
        self.zimg_len = len(d)

# kernel_work(gzip data):
#   Takes original gzip data, unpacks it using inbuilt zlib
#   patches by replacing a string, and then packs back modified one

    def kernel_work(self, gz_data):
        p7z_pack = [
            sz, 'a', 'dummy', '-tgzip', '-si', '-so', '-mx5', '-mmt4']
        printi('Unpacking kernel data...')
        kernel_data = zlib.decompress(gz_data, 16 + zlib.MAX_WBITS)
        if not kernel_data:
            raise Exception(
                "ERROR: Can't decompress GZIP data")
        if b'skip_initramfs' not in kernel_data:
            raise Exception(
                "ERROR: Didn't find skip_initramfs, no need to patch.")
        printi('Patching kernel data...')
        kernel_data = kernel_data.replace(b'skip_initramfs',  # basically everything
                                          b'want_initramfs')  # we were doing is for this
        printi('Packing kernel data...')
        p7zc = subprocess.run(p7z_pack, input=kernel_data, capture_output=True)
        if p7zc.returncode != 0:
            raise Exception(f'ERROR: p7z ended with an error. stderr: {p7zc.stderr}')
        self.new_gz_data = p7zc.stdout
        # Find proper end of gzip block by finding the size
        kernel_size = len(kernel_data)
        self.kernel_sz = struct.pack("I", kernel_size)
        self.new_gz_size = len(self.new_gz_data)

# join_zimg():
#   Takes all the results of previous work
#   gluing it together in a new modified zImage

    def join_zimg(self):
        printi('Getting all back together...')
        with io.BytesIO() as new_zimg_file:
            new_zimg_file.write(self.unp_data)  # unpacker code
            new_zimg_file.write(self.new_gz_data)  # patched kernel
            # Pad with zeroes (to satisfy piggy unpacker)
            new_zimg_file.write(b'\0' * (self.gz_size - self.new_gz_size))
            new_zimg_file.write(self.zimg_footer)  # dtbs and whatever is before/after
            new_zimg_file.seek(self.pos)
            # Write new gz size
            new_zimg_file.write(struct.pack("I", self.gz_begin +
                                            self.new_gz_size - 4))
            new_zimg_file.seek(0)
            return new_zimg_file.read()


if __name__ == "__main__":
    main()
