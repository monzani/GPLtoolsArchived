"""Low-level file operations when at least on file is on xrootd.
"""

import os

import runner

xrootStart = "root:"
xrootdLocation = os.getenv("GPL_XROOTD_DIR","/afs/slac.stanford.edu/g/glast/applications/xrootd/PROD/bin")
xrdcp    = xrootdLocation+"/xrdcp "
xrdstat  = xrootdLocation+"/xrd.pl -w stat "
xrdrm    = xrootdLocation+"/xrd.pl rm "
xrd      = xrootdLocation+"/xrd.pl"

## Set up message logging
import logging
log = logging.getLogger("gplLong")


def copy(fromFile, toFile):
    """
    @brief copy a staged file to final xrootd repository.
    @param fromFile = name of staged file, toFile = name of final file
    @return success code

    This just copies the file.
    """

    xrdcmd=xrdcp+" -np -f "+fromFile+" "+toFile   #first time try standard copy
    log.info("Executing...\n"+xrdcmd)
    rc = os.system(xrdcmd)
    log.debug("xrdcp return code = "+str(rc))
    
    return rc


def exists(fileName):
    xrdcmd = xrdstat + fileName
    xrdrc = os.system(xrdcmd)
    log.debug("xrdstat return code = " + str(xrdrc))
    rc = not xrdrc
    return rc


def getSize(fileName):
    xrdcmd = xrdstat + fileName
    pipe = os.popen(xrdcmd)
    lines = pipe.read()
    rc = pipe.close()
    if rc: return None
    log.debug(lines)
    size = int(lines.split()[1])
    return size


def makedirs(name, mode):
    return 0


def mkdirFor(fileName, mode):
    return 0


def remove(fileName):
    xrdcmd = '%s rm %s' % (xrd, fileName)
    rc = os.system(xrdcmd)  ## failure is Okay => file does not already exist
    return rc


def rmdir(name):
    return 0


def rmtree(name):
    xrdcmd = '%s rmtree %s' % (xrd, name)
    rc = runner.run(xrdcmd)
    return rc


def tempName(fileName):
    return fileName


def unTemp(fileName):
    return 0
