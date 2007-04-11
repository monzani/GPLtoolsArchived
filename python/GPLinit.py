#  GPLinit.py
"""@brief Initialize the GLAST PipeLine (GPL) python environment.
$Id$
1. Establish route to GPL module directory
2. Configure the message logger

Usage:

In the main script, execfile() this script, e.g.,

       execfile("/afs/slac/g/glast/ground/PipelineConfig/GPL2/python/GPLinit.py")

It is expected that immediately after this line, one also executes this:

       from GPL import *

Finally, in any script files called from __main__, one should add the single line:

       from GPL import *

@author T.Glanzman
26 Feb 2007
"""

import os
import sys

def init():
##
## Define production directory for module search and logger config
    try:
        GPL2 = os.environ['GPL2']
        print "GPLinit: Using $GPL2 location for GPLtools: ",GPL2
    except KeyError:
        GPL2 = "/afs/slac.stanford.edu/g/glast/ground/PipelineConfig/GPLtools/prod"
        print "GPLinit: Using hardwired default location for GPLtools: ",GPL2

    GPL2 = GPL2 + "/python"
    sys.path.insert(0, GPL2)


## Define (optional) debug directory for module search and logger config
##    and, define the logger configuration file
    try:
        GPL2debug = os.environ['GPL2_DEBUG']
        sys.path.insert(0, GPL2debug)
        configFile = GPL2debug+'/logger.cfg'
        print "GPLinit: Using $GPL2_DEBUG override location for GPLtools: ",GPL2debug
    except KeyError:
        configFile = GPL2+'/logger.cfg'
        

##
## Configure logging facility
    import logging.config
    logging.config.fileConfig(configFile)

    return

init()




