#  stageFiles.py
"""@brief Manage staging of files to/from machine-local disk.
$Id$
@author W. Focke <focke@slac.stanford.edu>

refactored: T.Glanzman 2/22/2007
"""

## Preliminaries
import os
import random
import re
import sys
import shutil
import time

## Set up message logging
import logging
log = logging.getLogger("gplLong")

filterAfs = '^/afs/'
filterAll = '.*'
filterNone = None


def waitABit(minWait=5, maxWait=10):
    delay = random.randrange(minWait, maxWait+1)
    log.info("Waiting %d seconds." % delay)
    time.sleep(delay)
    return


class StageSet:

    """@brief Manage staging of files to/from machine-local disk.

    simple example:
    > stagedStuff = StageSet()
    > sIn = stagedStuff.stageIn(inFile)
    > sOut = stagedStuff.stageOut(outFile)
    > os.system('do_something < %s > %s' % (sIn, sOut))
    > stagedStuff.finish()
    instead of:
    > os.system('do_something < %s > %s' % (inFile, outFile))

    The values returned by stageIn and stageOut may be the same as
    their inputs if staging is not possible.

    @todo Write out a persistent representation so that multiple processes
    could use the same staging set, and only the last one to run would
    call finish().  Or maybe have some way that processes could register
    a "hold" on the set, and calls to finish would have no effect until all
    holds had been released.

    @todo Allow user to write out "junk" files to the staging area and
    not needing or wanting to copy them back, and also for copying back
    any files that are found in the staging area at "finish" time.

    @todo Allow for the use of subdirectories of files in the staging
    area (e.g. the various Pulsar files that get produced by Gleam MC)



    
    """


    def __init__(self, stageName=None, stageArea=None, excludeIn=filterAfs,
                 excludeOut=filterNone, autoStart=True):
        """@brief Initialize the staging system
        @param [stageName] Name of directory where staged copies are kept.
        @param [stageArea] Parent of directory where staged copies are kept.
        @param [exculde] Regular expresion for file names which should not be staged.
        """

        log.debug("Entering stageFiles constructor...")
        self.setupFlag = 0
        self.setupOK = 0

        self.excludeIn = excludeIn
        self.excludeOut = excludeOut
        self.autoStart = autoStart
        
        ##
        ## defaultStateAreas defines all possible machine-local stage
        ## directories/partitions:
        ##
        ## SLAC batch machines all have /scratch for this purpose
        ## Desktop machines may or may not have /scratch
        ## Public machines (norics) do not have /scratch (only /tmp)
        
        defaultStageAreas=["/scratch","/tmp"]

        ##
        ## Construct path to staging area
        ## Priorities:
        ##  1     $GPL_STAGEROOTDEV (if defined)
        ##  2     Constructor argument
        ##  3     $GPL_STAGEROOT (if defined)
        ##  4     Selection from hard-wired default list
        try:
            envvarStageAreaDev = os.environ['GPL_STAGEROOTDEV']
            stageArea = envvarStageAreaDev
            log.debug('stageArea defined from $GPL_STAGEROOTDEV: '+stageArea)
        except KeyError:
            if stageArea is None:
                try:
                    envvarStageArea = os.environ['GPL_STAGEROOT']
                    stageArea = envvarStageArea
                    log.debug('stageArea defined from $GPL_STAGEROOT: '+stageArea)
                except KeyError:
                    for x in defaultStageAreas:
                        if os.access(x,os.W_OK):        # Does stageArea already exist?
                            log.debug("Successful access of "+x)
                            stageArea=x
                            log.debug('stageArea defined from default list: '+stageArea)
                            break
                        else:                           # Try to create stageArea
                            try:
                                os.makedirs(x)
                                stageArea=x
                                log.debug("Successful creation of "+x)
                                log.debug('stageArea defined from default list: '+stageArea)
                                break
                            except:                     # No luck, revert to $PWD
                                log.warning("Staging cannot use "+x)
                                stageArea=os.environ['PWD']
            else:
                log.debug('stageArea defined by constructor argument: '+stageArea)
    
                    
        log.debug("Selected staging root directory = "+stageArea)

        if stageName is None:
            stageName = `os.getpid()`    # aim for something unique if not specified
 
        self.stageDir = os.path.join(stageArea, stageName)
        log.debug('Targeted staging directory = '+self.stageDir)
        self.setup()

        return


    def setup(self):
        """@brief Create a staging area directory (intended as a private function)"""

        log.debug("Entering stage setup...")
        log.debug("os.access = "+`os.access(self.stageDir,os.F_OK)`)

        ## Check if requested staging directory already exists and, if
        ## not, try to create it
        if os.access(self.stageDir,os.F_OK):
            log.info("Requested stage directory already exists: "+self.stageDir)
            self.setupOK=1
            self.listStageDir()
        else:
            try:
                os.makedirs(self.stageDir)
                self.setupOK=1
                log.debug("Successful creation of "+self.stageDir)
##                 os.chmod(self.stageDir,'777')
##                 log.debug("Successful chmod to 777")
            except:
                log.warning('Staging disabled: error from os.makedirs: '+self.stageDir)
                self.stageDir=""
                self.setupOK=0

        log.debug("os.access = "+`os.access(self.stageDir,os.F_OK)`)
            
        ## Initialize file staging bookkeeping
        self.reset()
        self.setupFlag = 1
        return


    def reset(self):
        """@brief Initialize internal dictionaries/lists/counters
        (intended as a private function)"""
        self.stagedFiles = []
        self.numIn=0
        self.numOut=0
        self.xrootdIgnoreErrors = False

    def xrootdIgnore(self,flag):
        log.info("Setting xrootdIgnoreErrors to "+str(flag))
        self.xrootdIgnoreErrors = flag

    def stageIn(self, inFile):
        """@brief Stage an input file.
        @param inFile real name of the input file
        @return name of the staged file
        """
        if self.setupFlag <> 1: self.setup()

        if self.setupOK <> 1:
            log.warning("Stage IN not available for: "+inFile)
            return inFile
        elif self.excludeIn and re.search(self.excludeIn, inFile):
            log.info("Staging disabled for file '%s' by pattern '%s'." %
                     (inFile, self.excludeIn))
            return inFile
        else:
            cleanup = True
            stageName = self.stagedName(inFile)
            pass
        
        log.info("stageIn for: "+inFile)

        inStage = StagedFile(stageName, source=inFile,
                             cleanup=cleanup, autoStart=self.autoStart)

        self.numIn=self.numIn+1
        self.stagedFiles.append(inStage)

        return stageName

    
    def stageOut(self, *args):
        """@brief Stage an output file.
        @param outFile [...] = real name(s) of the output file(s)
        @return name of the staged file
        """
        if self.setupFlag <> 1: setup()

## Build stage file map even if staging is disabled - so that copying
## to possible 2nd target (e.g., xrootd) will still take place
        
        if not args:
            log.error("Primary stage file not specified")
            return ""

        outFile = args[0]
        destinations = args

        if self.setupOK <> 1:
            log.warning("Stage OUT not available for "+outFile)
            stageName = outFile
            cleanup = False
        elif self.excludeOut and re.search(self.excludeOut, outFile):
            log.info("Staging disabled for file '%s' by pattern '%s'." %
                     (outFile, self.excludeOut))
            stageName = outFile
            cleanup = False
        else:
            stageName = self.stagedName(outFile)
            log.info("stageOut for: "+outFile)
            cleanup = True
            pass

        outStage = StagedFile(
            stageName, destinations=destinations, cleanup=cleanup)
        self.stagedFiles.append(outStage)

        self.numOut=self.numOut+1

        return stageName


    def start(self):
        rc = 0
        for stagee in self.stagedFiles:
            rc |= stagee.start()
            continue
        return rc


    def finish(self,option=""):
        """@brief Delete staged inputs, move outputs to final destination.
        option: additional functions
        keep    - no additional function (in anticipation of further file use)
        clean   - +move/delete all staged files (in anticipation of further directory use)
        <null>  - +remove stage directories (full cleanup)
        wipe    - remove stage directories WITHOUT copying staged files to destination
        """
        log.debug('Entering stage.finish('+option+')')
        rc = 0     # overall

        keep = False
        
        ## bail out if no staging was done
        if self.setupOK == 0:
            log.warning("Staging disabled: look only if secondary target needs to receive produced file(s).")
        log.debug("*******************************************")

        if option == 'wipe':
            log.info(
                'Deleting staging directory without retrieving output files.')
            return self._removeDir()
        elif option == 'keep':
            keep = True
            pass

        # copy stageOut files to their final destinations
        for stagee in self.stagedFiles:
            rc |= stagee.finish(keep)
            continue

        if option == "keep": return rc              # Early return #1

        # Initialize stage data structures
        self.reset()

        if option == "clean": return rc           # Early return #2
                            
        # remove stage directory (unless staging is disabled)
        if self.setupOK <> 0:
            rc |= self._removeDir()
            
        self.setupFlag=0
        self.setupOK=0
        self.reset()
 
        return rc


    def _removeDir(self):

        # remove stage directory (unless staging is disabled)
        if self.setupOK <> 0:
            try:
                os.rmdir(self.stageDir)
                rc = 0
            except:
                log.warning("Staging directory not empty after cleanup!!")
                log.warning("Content of staging directory "+self.stageDir)
                os.system('ls -l '+self.stageDir)
                log.warning("*** All files & directories will be deleted! ***")
                try:
                    shutil.rmtree(self.stageDir)
                    rc = 0
                except:
                    log.error("Could not remove stage directory, "+self.stageDir)
                    rc = 2

        self.setupFlag=0
        self.setupOK=0
        self.reset()
 
        return rc



    def stagedName(self, fileName):
        """@brief Generate names of staged files.
        @param fileName Real name of file.
        @return Name of staged file.
        """
        base = os.path.basename(fileName)
        stageName = os.path.join(self.stageDir, base)
        return stageName



### Utilities:  General information about staging and its files


    def getStageDir(self):
        """@brief Return the name of the stage directory being used
        """
        if self.setupOK == 0: return ""
        return self.stageDir



    def listStageDir(self):
        """@brief List contents of current staging directory"""
        if self.setupOK == 0: return
        log.info("\nContents of stage directory \n ls -laF "+self.stageDir)
        dirlist = os.system('ls -laF '+self.stageDir)
        return


    def getStageStatus(self):
        """@brief Return status of file staging
        0 = staging not in operation
        1 = staging initialized and in operation
        """
        return self.setupOK



    def dumpStagedFiles(self):
        """@brief Dump names of staged files to stdout"""
        print '\n\n\tStatus of File Staging System'
        print 'setupFlag= ',self.setupFlag,', setupOK= ',self.setupOK,', stageDirectory= ',self.stageDir,'\n'
        print self.numIn," files in stagedIn map:"
        ix=1
        while ix <= self.numIn:
            foo = self.realInFiles[ix]
            foo2 = self.inFiles.get(foo)
            print foo," --> ",foo2
            ix = ix + 1
            
        print self.numOut," files in stageOut map:"
        ix=1
        while ix <= self.numOut:
            foo1 = self.realOutFiles[ix]
            foo2 = self.realOutFiles2[ix]
            foo3 = self.outFiles.get(foo1)
            if foo2 == "":
                print foo1," <-- ",foo3
            else:
                print foo1," & "
                print foo2," <-- ",foo3
            ix = ix + 1

        print '\n\n'
        sys.stdout.flush()


    def dumpFileList(self,filename):
        """@brief Dump a complete list of
        produced & staged output files to disk - for cleaning up these
        files during rollback"""

        ## Open/Create disk file
        try:
            foo = open(filename,'w')
        except:
            log.error("Could not create dumpFileList "+filename+"\n foo = "+foo)
            return 1

        ## Write full filenames to dump file
        for item in self.realOutFiles.items():
            index = item[0]
            realName = item[1]
            log.debug("realName= "+realName)
            foo.write(realName+"\n")

        for item in self.realOutFiles2.items():
            index = item[0]
            realName = item[1]
            if len(realName) > 0:
                log.debug("realName= "+realName)
                foo.write(realName+"\n")

        ## close file
        foo.close()
        return
    
    pass


class StagedFile(object):

    def __init__(self, location, source=None, destinations=[],
                 cleanup=False, autoStart=True):
        self.source = source
        self.location = location
        self.destinations = list(destinations)
        self.cleanup = cleanup
        self.started = False
        if location in self.destinations:
            self.destinations.remove(location)
            self.cleanup = False
            pass
        if autoStart:
            self.start()
            pass
        self.dumpState()
        return

    def dumpState(self):
        log.info('StagedFile 0x%x' % id(self))
        log.info('source: %s' % self.source)
        log.info('location: %s' % self.location)
        log.info('destinations: %s' % self.destinations)
        log.info('cleanup: %s' % self.cleanup)
        log.info('started: %s' % self.started)
        return

    def start(self):
        self.dumpState()
        rc = 0
        if self.source and self.location != self.source and not self.started:
            rc = copy(self.source, self.location)
            pass
        self.started = True
        return rc

    def finish(self, keep=False):
        self.dumpState()
        rc = 0
        for dest in self.destinations:
            rc |= copy(self.location, dest)
            continue
        if not keep and self.cleanup and os.access(self.location, os.W_OK):
            log.info('Nuking %s' % self.location)
            os.remove(self.location)
        else:
            log.info('Not nuking %s' % self.location)
            pass
        return rc
    
    pass


xrootStart = "root:"
def copy(fromFile, toFile):
    rc = 0

    if toFile == fromFile:
        log.info("Not copying %s to itself." % fromFile)
        return rc

    if fromFile.startswith(xrootStart) or toFile.startswith(xrootStart):
        rc = xrootdCopy(fromFile, toFile)
    else:
        rc = fileCopy(fromFile, toFile)
        pass
    
    return rc


def xrootdCopy(fromFile, toFile):
    """
    @brief copy a staged file to final xrootd repository.
    @param fromFile = name of staged file, toFile = name of final file
    @return success code
    """
    rc = 0
    rcx1 = 0
    rcx2 = 0

    xrdcp ="~glastdat/bin/xrdcp -np "   #first time try plain copy
    xrdcmd=xrdcp+fromFile+" "+toFile
    log.info("Executing:\n"+xrdcmd)
    # Alternate way to run xrdcp without the error message being displayed
    fd = os.popen3(xrdcmd,'r')    # Capture output from unix command
    foo = fd[2].read()
    fd[0].close()
    fd[1].close()
    fd[2].close()
    rcx1 = len(foo)      # If xrdcp emits *any* stderr message, interpret as error
##
## We must try to copy into xrootd a second time if the first fails.  That is
##  because xrdcp has a silly "overwrite" option: it must only be used if the
##  file already exists, but not otherwise.  So, in the case we're overwriting
##  the first attempt will fail, but the second should succeed.
##
    if rcx1 != 0:        # This may just mean the file already exists
        #            log.warning("xrdcp failure: rcx1 = "+str(rcx1)+", for file "+toFile)
        xrdcmd=xrdcp+" -f "+fromFile+" "+toFile #2nd time try overwrite copy
        log.info("Executing:\n"+xrdcmd)
        fd = os.popen3(xrdcmd,'r')    # Capture output from unix command
        foo = fd[2].read()
        fd[2].close()
        fd[1].close()
        fd[0].close()
        log.debug("Captured output from xrdcp command:\n"+foo)
        rcx2 = len(foo)      # If xrdcp emits *any* message, interpret as error
        log.debug("Length of response = "+str(rcx2))
                        
        if rcx2 != 0:     # This is likely a genuine error
            log.warning("xrdcp -f failure: rcx2 = "+str(rcx2)+", for file "+toFile)
            log.error("xrootd failure: could not copy file "+fromFile)
            rc += 1
            pass
        pass
    return rc


def fileCopy(fromFile, toFile):
    """
    @brief copy a file
    @param fromFile = name of ssource file
    @param toFile = name of destination file
    @return success code
    """
    maxtry = 5
    mytry = 1
    rc=0

## To allow for possible filesystem failures (e.g. delay to
## automount), several attempts are made to copy the input file to
## local scratch space.  If that fails, then staging is effectively
## disabled for that file.

    while mytry < maxtry:
        start = time.time()

        try:
            log.info("Executing:\ncp "+fromFile+" "+toFile)
            shutil.copy(fromFile,toFile)
            mytry = maxtry
        except:
            log.error("Error copying file to %s (try %d)" %
                      (toFile, mytry))
            waitABit()
            mytry = mytry + 1
            if mytry == maxtry: rc=1
            continue
        continue

    deltaT = time.time() - start
    size = os.stat(toFile).st_size
    if deltaT:
        rate = '%g' % (float(size) / deltaT)
    else:
        rate = 'many'
        pass
    log.info('Transferred %g bytes in %g seconds, avg. rate = %s B/s' %
             (size, deltaT, rate))
    return rc


