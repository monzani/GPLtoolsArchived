#!/afs/slac/g/glast/isoc/flightOps/rhel3_gcc32/ISOC_PROD/bin/shisoc python2.5

"""@brief Interface to pipeline functions.
"""

import sys

import runner

maxVarLength = 1000

def setVariable(varName, value):
    # use bash function
    value = str(value)
    if len(value) > maxVarLength:
        print >> sys.stderr, 'Variable is probably too long to work correctly (max %s).' % maxVarLength
        pass
    cmd = "pipelineSet %s '%s'" % (varName, value)
    status = runner.run(cmd)
    return status

def createSubStream(subTask, stream=-1, args=''):
    cmd = "pipelineCreateStream %s %s '%s'" % (subTask, stream, args)
    status = runner.run(cmd)
    return status
