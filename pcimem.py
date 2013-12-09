#!/usr/bin/env python2

import mmap
import os
import struct
import sys

if len(sys.argv) < 4:
    sys.exit('Usage: ./pcimem.py sysfile r|w offset [data]')

sysfile = sys.argv[1]
rw = sys.argv[2]
offset = long(sys.argv[3])

if not os.path.isfile(sysfile):
    sys.exit('{} is not a valid file descriptor!'.format(sysfile))

if rw == 'w' and len(sys.argv) < 5:
    sys.exit('Missing data for w command!')

with open(sysfile, os.O_RDWR | os.O_SYNC) as fd:
    mm = mmap.mmap(
        fd.fileno(),
        mmap.PAGESIZE,
        mmap.MAP_SHARED,
        mmap.PROT_READ | mmap.PROT_WRITE,
        offset=(offset & ~(mmap.PAGESIZE-1)),
    )

    mm.seek(offset)

    # read 32-bit data
    if rw == 'r':
        rdata, = struct.unpack('I', mm.read(4))
        print('[{:04x}] => {:04x}'.format(offset, rdata))
    elif rw == 'w':
        wdata = long(sys.argv[4])
        mm.write(struct.pack('I', wdata))
        print('[{:04x}] <= {:04x}'.format(offset, wdata))

    mm.close()

