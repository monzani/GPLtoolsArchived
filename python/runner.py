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
    print >> sys.stderr, "About to run [%s] at %s" % (cmd, time.asctime())
    print >> sys.stderr, '---------------- start log ----------------'
    cstart = time.clock()
    wstart = time.time()
    status = os.system(cmd)
    cstop = time.clock()
    wstop = time.time()
    print >> sys.stderr, '----------------  end log  ----------------'
    print >> sys.stderr, "Status was %s at %s" % (status, time.asctime())
    print >> sys.stderr, 'CPU:  %f' % (cstop - cstart)
    print >> sys.stderr, 'Wall: %f' % (wstop - wstart)
    return status
