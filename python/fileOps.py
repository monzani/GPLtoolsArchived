"""Generic high-level file operations.
"""


import random
import sys
import time

import fsFileOps
import xrootdFileOps

## Set up message logging
import logging
log = logging.getLogger("gplLong")

dirMode = 0755

maxtry = 5
minWait = 5
maxWait = 10

xrootStart = "root:"


def waitABit(minDelay=None, maxDelay=None):
    if minDelay is None: minDelay = minWait
    if maxDelay is None: maxDelay = maxWait
    delay = random.randrange(minDelay, maxDelay+1)
    log.info("Waiting %d seconds." % delay)
    time.sleep(delay)
    return


def whichImplementation(*fileNames):
    anyXrootd = any(map(isOnXrootd, fileNames))
    if anyXrootd:
        impl = xrootdFileOps
    else:
        impl = fsFileOps
        pass
    return impl


def isOnXrootd(fileName):
    return fileName.startswith(xrootStart)


def _makeWrapper(funcName):
    """A lot of funtions here just pick the implementation and call
    the appropriate funtion, passing along arguments and return value
    unmodified. This generates wrappers that do that.
    Note that all positional arguments must be file or directory names,
    any others must use keywords.
    """
    def wrapper(*args, **kwargs):
        impl = whichImplementation(*args)
        funk = getattr(impl, funcName)
        rc = funk(*args, **kwargs)
        return rc
    return wrapper



def copy(fromFile, toFile, maxTry=None):
    """
    @brief copy a file
    @param fromFile = name of ssource file
    @param toFile = name of destination file
    @return success code

    This does retries, logging, and performs various checks.
    """
    if maxTry is None: maxTry = maxtry
    
    rc = 0

    if toFile == fromFile:
        log.info("Not copying %s to itself." % fromFile)
        return rc

    impl = whichImplementation(fromFile, toFile)

    tn = tempName(toFile)

    log.info("Copying %s to %s " % (fromFile, tn))

    # To allow for possible filesystem failures (e.g. delay to
    # automount), several attempts are made to copy the input file to
    # local scratch space.  If that fails, then staging is effectively
    # disabled for that file.
    for mytry in range(maxTry):
        if mytry: waitABit()
        rc = 0
        start = time.time()

        log.info('Starting try %d.' % mytry)

        # Verify source file is accessible and get its size
        fromSize = getSize(fromFile)
        if fromSize is None:
            log.error('%s does not exist!' % fromFile)
            rc |= 1
            continue

        try:
            # The following kludge is necessary (11/4/2008) due to bug in xrdcp
            #  wherein overwriting an existing file on a "full" server will fail
            #  The fix is to first delete the file.  
            log.debug("Attempting to remove destination file")
            remove(toFile)
            if tn != toFile: remove(tn)

            rc |= mkdirFor(tn)
            rc |= impl.copy(fromFile, tn)
        except OSError:
            ex, exInfo = sys.exc_info()[:2]
            rc = 1
            log.error("Error copying file to %s (try %d): %s %s" %
                      (tn, mytry, ex, exInfo))
            continue

        if rc: continue
        
        deltaT = time.time() - start
        
        # Verify destination file has been copied
        toSize = getSize(tn)
        if toSize is None:
            log.error('%s does not exist!' % tn)
            rc = 1
            continue

        if toSize != fromSize:
            msg = 'Size mismatch!\n%d: %s\n%d %s' % \
                  (fromSize, fromFile, toSize, tn)
            log.error(msg)
            rc = 1
            continue

        rc |= unTemp(toFile)
        
        log.debug('Try %d rc: %d' % (mytry,rc))
        if not rc: break
        continue

    if rc:
        log.info('Failed after %d tries' % (mytry+1))
        return 1
    
    log.info('Succeeded after %d tries' % (mytry+1))

    if deltaT:
        rate = '%g' % (float(toSize) / deltaT)
    else:
        rate = 'many'
        pass
    log.info('Transferred %g bytes in %g seconds, avg. rate = %s B/s' %
             (toSize, deltaT, rate))

    return rc


def exists(fileName):
    log.info("Verifying existence of " + fileName)
    impl = whichImplementation(fileName)
    rc = impl.exists(fileName)
    if not rc: log.error("Could not access requested file: " + fileName)
    return rc


getSize = _makeWrapper('getSize')


def makedirs(name, mode=None):
    if mode is None: mode = dirMode
    impl = whichImplementation(name)
    rc = impl.makedirs(name, mode)
    return rc


def mkdirFor(name, mode=None):
    if mode is None: mode = dirMode
    impl = whichImplementation(name)
    rc = impl.mkdirFor(name, mode)
    return rc


remove = _makeWrapper('remove')

rmdir = _makeWrapper('rmdir')

rmtree = _makeWrapper('rmtree')

tempName = _makeWrapper('tempName')

unTemp = _makeWrapper('unTemp')
