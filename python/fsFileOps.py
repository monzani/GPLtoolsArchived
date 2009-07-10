"""Low-level file operations when all files involved are on a regular
filesystem.
"""

import errno
import os

import cpck
import runner

## Set up message logging
import logging
log = logging.getLogger("gplLong")


def copy(fromFile, toFile):
    """
    @brief copy a file
    @param fromFile = name of ssource file
    @param toFile = name of destination file
    @return success code - actually always 0, raises exceptions on failure.

    This just copies the file.
    """
    checksum = cpck.copyAndSum(fromFile, toFile)
    log.info('Checksum = %s' % checksum)
    return 0


def exists(fileName):
    rc = os.access(fileName, os.R_OK)
    return rc


def getSize(fileName):
    try:
        rc = os.stat(fileName).st_size
    except OSError, e:
        if e.errno != errno.ENOENT: raise
        rc = None
    return rc


def makedirs(name, mode):
    """makedirs(path,  mode)

    Super-mkdir; create a leaf directory and all intermediate ones.
    Works like mkdir, except that any intermediate path segment (not
    just the rightmost) will be created if it does not exist.  This is
    recursive.

    This is a modified version of os.makedirs that's more careful to not
    try to make directories that already exist. So it probably inherits the
    Python2.5 license.

    """
    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    if head and tail and not os.path.exists(head):
        try:
            makedirs(head, mode)
        except OSError, e:
            # be happy if someone already created the path
            if e.errno != errno.EEXIST: raise
        if tail == os.curdir:     # xxx/newdir/. exists if xxx/newdir exists
            return
    if not os.path.exists(name):
        try:
            os.mkdir(name, mode)
        except OSError, e:
            # be happy if someone already created the path
            if e.errno != errno.EEXIST: raise
            pass
        pass
    return


def mkdirFor(filePath, mode):
    status = 0
    dirPath = os.path.dirname(filePath)
    if not os.path.isdir(dirPath):
        log.info('Making directory %s' % dirPath)
        makedirs(dirPath, mode)
        pass
    return status


def remove(fileName):
    try:
        os.remove(fileName)
        rc = 0
    except OSError, e:
        if e.errno != errno.ENOENT: raise
        rc = 1
    return rc


def rmdir(name):
    os.rmdir(name)
    return 0


def rmtree(name):
    cmd = 'rm -rf %s' % name
    rc = runner.run(cmd)
    return rc


def tempName(fileName):
    tn = fileName + '.part'
    return tn


def unTemp(fileName):
    tn = tempName(fileName)
    log.info("Renaming %s to %s" % (tn, fileName))
    os.rename(tn, fileName)
    return 0
