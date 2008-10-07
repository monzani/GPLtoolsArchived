#!/usr/bin/env python2.5

import hashlib
import optparse
import os
import sys
import threading
import time
import Queue


defaultBlock = 2**15
defaultPool = 2**20
defaultDepth = defaultPool / defaultBlock

def timeCopy(fun, inFile, outFile):
    size = os.stat(inFile).st_size / 1e6
    start = time.time()
    result = fun(inFile, outFile)
    stop = time.time()
    delta = stop - start
    rate = size / delta
    print fun, size, delta, rate, result
    return


def main():
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    inFile, outFile = args
    for fun in [threadCopy, osCopy, dumbCopy, osSumI, osSumO, dumbSum]:
        cmd = 'fs flush %s' % inFile
        os.system(cmd)
        result = timeCopy(fun, inFile, outFile)
        os.unlink(outFile)
        #print result
        continue
    return


def writer(ofp, q):
    while True:
        block = q.get()
        ofp.write(block)
        q.task_done()
        continue
    return

def reader(q):
    """not implemented"""
    return

def summer(hasher, inQ, outQ):
    """junk"""
    data = getBlock()
    hasher.update(data)
    putBlock(data)
    return


def dumbCopy(inFile, outFile):
    reader = readIt(inFile)
    ofp = open(outFile, 'wb')
    for block in reader:
        ofp.write(block)
        continue
    ofp.close()
    return

def dumbSum(inFile, outFile):
    """Copy a file, performing an md5 checksum on the fly.
    The input file is read once, the output file not at all.
    Return value is a string containing the hex representation of the sum.
    """
    summer = hashlib.md5()
    reader = readIt(inFile)
    ofp = open(outFile, 'wb')
    for block in reader:
        summer.update(block)
        ofp.write(block)
        continue
    ofp.close()
    digest = summer.hexdigest()
    return digest


def osCopy(inFile, outFile):
    cmd = 'cp %s %s' % (inFile, outFile)
    os.system(cmd)
    return

def osSumO(inFile, outFile):
    cmd = 'cp %s %s' % (inFile, outFile)
    os.system(cmd)
    cmd = 'md5sum %s' % outFile
    digest = os.popen(cmd).read().split()[0]
    return digest

def osSumI(inFile, outFile):
    cmd = 'cp %s %s' % (inFile, outFile)
    os.system(cmd)
    cmd = 'md5sum %s' % inFile
    digest = os.popen(cmd).read().split()[0]
    return digest


def threadCopy(inFile, outFile):
    q = Queue.Queue(defaultDepth)
    reader = readIt(inFile)
    ofp = open(outFile, 'wb')
    t = threading.Thread(target=writer, args=(ofp, q))
    t.setDaemon(True)
    t.start()
    for block in reader:
        q.put(block)
        continue
    q.join()
    ofp.close()
    return


class readIt(object):

    def __init__(self, inFile, blockSize=defaultBlock):
        self.ifp = open(inFile, 'rb')
        self.blockSize = blockSize
        return

    def next(self):
        block = self.ifp.read(self.blockSize)
        if not block:
            self.ifp.close()
            raise StopIteration
        return block

    def __iter__(self):
        return self

    pass


copyAndSum = dumbSum


if __name__ == "__main__":
    main()
    
