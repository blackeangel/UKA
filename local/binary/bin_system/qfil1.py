import os
import sys
import xml.etree.ElementTree
from typing import IO


class Qfil(object):
    def __init__(self):
        self.target_dir = None
        self.list_work = []
        self.out_file = None
        self.name = None
        self.buffer = 8192
        self.sektor_size = 512

    def _parse_xml(self, file_path, name_label):
        e = xml.etree.ElementTree.parse(file_path).getroot()
        for item in e.findall('program'):
            if item.get('label') == name_label or item.get('label') == name_label + '_a':
                if self.name is None:
                    self.name = item.get('label').rsplit('_a', 1)[0]+'.raw.img'
                self.list_work.append(item)

    @staticmethod
    def _read_chunks(fd: IO, chunk_size: int = 8192):
        while True:
            data = fd.read(chunk_size)
            if not data:
                break
            yield data

    def _copy_img(self, filename, seek):
        cur_pos = self.out_file.tell()
        if cur_pos != 0:
            for i in range(int((seek * self.sektor_size - cur_pos)/self.sektor_size)):
                self.out_file.write(b'\0' * self.sektor_size)
        try:
            with open(filename, 'rb', buffering=self.buffer) as orig_file:
                for chunk in self._read_chunks(orig_file):
                    self.out_file.write(chunk)
                    self.out_file.flush()
        except FileNotFoundError:
            os.unlink(self.out_file)
            print(f'File "{os.path.basename(filename)}" not found in directory '
                  f'"{self.target_dir}". Unpacking is\'t possible.')
            sys.exit(0)

    def convert(self, file_path, name_label):
        offset = 0
        self.target_dir = os.path.dirname(file_path)
        self._parse_xml(file_path, name_label)
        self.out_file = open(self.target_dir + os.sep + self.name, 'wb+', buffering=self.buffer)
        for item in self.list_work:
            start_sector = int(item.get('start_sector'))
            self.sektor_size = int(item.get('SECTOR_SIZE_IN_BYTES'))
            filename = self.target_dir + os.sep + item.get('filename')
            if offset == 0:
                offset = start_sector
            seek = start_sector - offset
            self._copy_img(filename, seek)
        self.out_file.close()
        return self.target_dir + os.sep + self.name


if __name__ == '__main__':
    if sys.argv.__len__() == 3:
        Qfil().convert(sys.argv[1], sys.argv[2])
