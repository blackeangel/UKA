#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ====================================================
#          FILE: img2sdat.py
#       AUTHORS: xpirt - luxi78 - howellzhu
#          DATE: 2018-01-05 15:21:47 CEST
#       Moded by blackeangel 4pda.ru on 1.6 version
# ====================================================

from __future__ import print_function

import sys, os, errno, tempfile
import common, blockimgdiff, sparse_img

__version__ = '1.6'

if sys.hexversion < 0x02070000:
    print >> sys.stderr, "Python 2.7 or newer is required."
    try:
       input = raw_input
    except NameError: pass
    input('Press ENTER to exit...')
    sys.exit(1)
else:
    print('img2sdat binary - version: %s\n' % __version__)

try:
    INPUT_IMAGE = str(sys.argv[1])
except IndexError:
    print('Usage: img2sdat.py <system_img> [outdir] [version]\n')
    print('    <system_img>: input system image\n')
    print('    [outdir]: output directory (current directory by default)\n')
    print('    [version]: transfer list version number, will be asked by default - more info on xda thread)\n')
    print('Visit xda thread for more information.\n')
    try:
       input = raw_input
    except NameError: pass
    input('Press ENTER to exit...')
    sys.exit()

def __AndroidVersion():
    global input
    item = True
    while item:
        print('''1. Android Lollipop 5.0
2. Android Lollipop 5.1
3. Android Marshmallow 6.0
4. Android 7.x/8.x/9.x/10.x/11.x
''')
        try:
            input = raw_input
        except NameError:
            pass
        item = input('Choose system version: ')
        if item == '1':
            version = 1
            break
        elif item == '2':
            version = 2
            break
        elif item == '3':
            version = 3
            break
        elif item == '4':
            version = 4
            break
        else:
            return
    return version

def __FindStringInByteFile(word,file):
    findword =  bytes(word, 'utf-8')
    with open(file, "r+b") as f:
        for line in f:
            if findword in line:
                rez=line.__str__()[2:len(line.__str__())-3] #получаем строку без b' вначале и \n' в конце строки
                return rez.split("=")[1] #для текущей задачи сплит

def __convertApi2ver(versionApi):
    if versionApi == "None":
        ver = 0
    elif versionApi == "21":
        ver=1
    elif versionApi =="22":
        ver=2
    elif versionApi =="23":
        ver=3
    elif versionApi =="24" or versionApi =="25" or versionApi =="26" or versionApi =="27" or versionApi =="28" or versionApi =="29":
        ver=4
    return

def main(argv):
    global input
    if len(sys.argv) > 2 and len(sys.argv) < 4:
        if sys.argv[len(sys.argv)-1].isdigit():
            if int(sys.argv[len(sys.argv)-1]) < 5:
                version = int(sys.argv[len(sys.argv)-1])
                outdir = os.path.realpath(os.path.dirname(sys.argv[1])) + os.sep + os.path.basename(sys.argv[1]).split('.')[0]
            else:
                outdir = sys.argv[len(sys.argv)-1] + os.sep + os.path.basename(sys.argv[1]).split('.')[0]
                if not os.path.exists(sys.argv[len(sys.argv)-1]):
                    os.makedirs(sys.argv[len(sys.argv)-1])
                versionsdk = __FindStringInByteFile("ro.build.version.sdk=", sys.argv[1]).__str__()
                print('Detected version sdk %s' % versionsdk)
                version = __convertApi2ver(versionsdk)
                if version == 0:
                    version = __AndroidVersion()
        else:
            outdir = sys.argv[len(sys.argv) - 1] + os.sep + os.path.basename(sys.argv[1]).split('.')[0]
            if not os.path.exists(os.path.dirname(sys.argv[len(sys.argv) - 1])):
                os.makedirs(sys.argv[len(sys.argv) - 1])
            versionsdk = __FindStringInByteFile("ro.build.version.sdk=", sys.argv[1]).__str__()
            print('Detected version sdk %s' % versionsdk)
            version = __convertApi2ver(versionsdk)
            if version == 0:
                version = __AndroidVersion()
    else:
        if len(sys.argv) == 2:
            if sys.argv[len(sys.argv) - 1].isdigit():
                if int(sys.argv[len(sys.argv) - 1]) < 5:
                    version = int(sys.argv[len(sys.argv)-1])
                    outdir = os.path.realpath(os.path.dirname(sys.argv[1])) + os.sep + os.path.basename(sys.argv[1]).split('.')[0]
            else:
                    outdir = os.path.realpath(os.path.dirname(sys.argv[1])) + os.sep + os.path.basename(sys.argv[1]).split('.')[0]
                    versionsdk = __FindStringInByteFile("ro.build.version.sdk=", sys.argv[1]).__str__()
                    print('Detected version sdk %s' % versionsdk)
                    version = __convertApi2ver(versionsdk)
                    if version == 0:
                        version = __AndroidVersion()
        else:
                if int(sys.argv[len(sys.argv) - 1]) < 5:
                    version = int(sys.argv[len(sys.argv) - 1])
                else:
                    versionsdk = __FindStringInByteFile("ro.build.version.sdk=", sys.argv[1]).__str__()
                    print('Detected version sdk %s' % versionsdk)
                    version = __convertApi2ver(versionsdk)
                    if version == 0:
                        version = __AndroidVersion()
                outdir = sys.argv[2] + os.sep + os.path.basename(sys.argv[1]).split('.')[0]
                if not os.path.exists(sys.argv[2]):
                    os.makedirs(sys.argv[2])


    # Get sparse image
    image = sparse_img.SparseImage(INPUT_IMAGE, tempfile.mkstemp()[1], '0')

    # Generate output files
    b = blockimgdiff.BlockImageDiff(image, None, version)
    b.Compute(outdir)

    print('Done! Output files: %s' % os.path.dirname(outdir))
    return


if __name__ == '__main__':
    main(sys.argv)
