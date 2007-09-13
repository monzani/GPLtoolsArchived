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
    default = "yes"
    try:
        GPL2 = os.environ['GPL2']
        GPL2 = GPL2.rstrip('/')   # remove trailing "/", if any
        default = "no"
        sys.stdout.flush()
#        os.system("ls -ld "+GPL2)
        GPL2o = GPL2
    except KeyError:
        GPL2 = "/afs/slac.stanford.edu/g/glast/ground/PipelineConfig/GPLtools/prod"
#        os.system("ls -ld "+GPL2)
        GPL2o = GPL2

    GPL2 = GPL2 + "/python"
    sys.path.insert(0, GPL2)

    # Add a directory to sys.path that will give us access to the ISOC
    # installation of the LBL Netlogger package (as
    # lbl.dsd.netlogger.nllite).
    sys.path.insert(0, "/afs/slac.stanford.edu/g/glast/isoc/flightOps/volumes/vol1/rhel4_gcc34/install_20070612/lib/python2.5/site-packages/gov/")


## Define (optional) debug directory for module search and logger config
##    and, define the logger configuration file
    GPL_debug = "no"
    try:
        GPL2debug = os.environ['GPL2_DEBUG']
        sys.path.insert(0, GPL2debug)
        configFile = GPL2debug+'/logger.cfg'
        GPL_debug = "yes"
    except KeyError:
        configFile = GPL2+'/logger.cfg'
    sys.stdout.flush()
        

##
## Configure logging facility
    import logging.config
    logging.config.fileConfig(configFile)


    import logging
    log = logging.getLogger("gplLong")

#    log.info("Created logger 'gplLong'")
    
    try:
        debuglvl = os.environ['GPL2_DEBUGLVL']
    except:
        debuglvl = "DEBUG"

#    log.info("debuglvl = "+debuglvl)

    if debuglvl == "INFO":
        log.setLevel(logging.INFO)
#        log.info("Setting log level to INFO")
        

    if default == "yes":
        log.debug("Using default location for GPLtools: "+GPL2)
    else:
        log.debug("Using GPLtools from user-specified $GPL2 "+GPL2)

    if debuglvl == "DEBUG":os.system("ls -ld "+GPL2o)
    
    if GPL_debug == "yes":
        log.debug("Using $GPL2_DEBUG override location for GPLtools: "+GPL2debug)


    return

init()




