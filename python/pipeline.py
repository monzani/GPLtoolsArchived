#!/sdf/data/fermi/a/isoc/flightOps/rhel6_gcc44/ISOC_PROD/bin/shisoc python2.6

"""@brief Interface to pipeline functions.
"""

import os
import sys

import runner

maxVarLength = 1000
def setVariable(varName, value):
    value = str(value)
    if len(value) > maxVarLength:
        print >> sys.stderr, 'Variable is probably too long to work correctly (max %s).' % maxVarLength
        pass

    with open(os.environ["PIPELINE_SUMMARY"], "a") as f:
        f.write("Pipeline.%s: %s\n" %(varName, value))


def createSubStream(subTask, stream=-1, args=''):

    with open(os.environ["PIPELINE_SUMMARY"], "a") as f:
        f.write("PipelineCreateStream.%s.%d: %s\n" %(subTask, int(stream), args))


def getProcess():
    return os.environ['PIPELINE_PROCESS']


def getStream():
    return os.environ['PIPELINE_STREAM']


def getTask():
    return os.environ['PIPELINE_TASK']
