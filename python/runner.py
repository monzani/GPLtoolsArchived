"""@brief Run external programs.

@author W. Focke <focke@slac.stanford.edu>
"""

import os
import sys
import time

def run(cmd):
    """@brief Run an external command (like os.system(), plus some logging).
    @param cmd The command to run.
    """
    print >> sys.stderr, '---------------- start commentary ----------------'
    print >> sys.stderr, "About to run [%s] at %s" % (cmd, time.asctime())
    print >> sys.stderr, '---------------- start log ----------------'
    cstart = time.clock()
    wstart = time.time()
    status = os.system(cmd)
    cstop = time.clock()
    wstop = time.time()
    print >> sys.stderr, '----------------  end log  ----------------'
    print >> sys.stderr, "Ended at %s" % time.asctime()
    print >> sys.stderr, "Raw status = %d" % status
    cookedStatus = status >> 8
    print >> sys.stderr, "Exit code = %d" % cookedStatus
    signal = status & 127
    if signal: print >> sys.stderr, "Signal = %d" % signal
    coreDump = status & 128
    if coreDump: print >> sys.stderr, "Core dumped."
    print >> sys.stderr, 'CPU:  %f' % (cstop - cstart)
    print >> sys.stderr, 'Wall: %f' % (wstop - wstart)
    print >> sys.stderr, '----------------  end commentary  ----------------'
    returnStatus = cookedStatus | signal
    return returnStatus
