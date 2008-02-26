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

import runner

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
                                pass
                            pass
                        pass
                    pass
                pass
            
            else:
                log.debug('stageArea defined by constructor argument: '+stageArea)
                pass
                    
        log.debug("Selected staging root directory = "+stageArea)

        if stageName is None:
            stageName = `os.getpid()`    # aim for something unique if not specified
            pass
 
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
                pass
            pass
        
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
        self.numMod=0
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
        
        log.info("\nstageIn for: "+inFile)

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
            log.info("\nstageOut for: "+outFile)
            cleanup = True
            pass

        outStage = StagedFile(
            stageName, destinations=destinations, cleanup=cleanup)
        self.stagedFiles.append(outStage)

        self.numOut=self.numOut+1

        return stageName








    def stageMod(self, modFile):
        """@brief Stage a in a file to be modified and then staged out
        @param modFile real name of the target file
        @return name of the staged file
        """
        if self.setupFlag <> 1: self.setup()

        if self.setupOK <> 1:
            log.warning("Stage MOD not available for: "+modFile)
            return modFile
        elif self.excludeIn and re.search(self.excludeIn, modFile):
            log.info("Staging disabled for file '%s' by pattern '%s'." %
                     (modFile, self.excludeIn))
            return modFile
        else:
            cleanup = True
            stageName = self.stagedName(modFile)
            pass
        
        log.info("\nstageMod for: "+modFile)

        modStage = StagedFile(stageName, source=modFile, destinations=[modFile],
                             cleanup=cleanup, autoStart=self.autoStart)

        self.numMod += 1
        self.stagedFiles.append(modStage)

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
        log.info("Initializing internal staging structures")
        self.reset()

        if option == "clean": return rc           # Early return #2
                            
        # remove stage directory (unless staging is disabled)
        if self.setupOK <> 0:
            rc |= self._removeDir()
            pass
        
        self.setupFlag=0
        self.setupOK=0
        self.reset()
 
        return rc


    def _removeDir(self):

        # remove stage directory (unless staging is disabled)
        if self.setupOK <> 0:
            try:
                os.rmdir(self.stageDir)
                log.info("Removed staging directory "+str(self.stageDir))
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
                    pass
                pass
            pass
 
    
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


    def getChecksums(self,printflag=None):
        """@brief Return a dictionary of: [stagedOut file name,[length,checksum] ].  Call this after creating file(s), but before finish(), if at all.  If the printflag is set to 1, a brief report will be sent to stdout."""
        cksums = {}
        # Compute checksums for all stagedOut files
        log.info("Calculating 32-bit CRC checksums for stagedOut files")
        for stagee in self.stagedFiles:
            if len(stagee.destinations) != 0:
                file = stagee.location
                if os.access(file,os.R_OK):
                    cksum = "cksum "+file
                    fd = os.popen(cksum,'r')    # Capture output from unix command
                    foo = fd.read()             # Calculate checksum
                    rc = fd.close()
                    if rc != None:
                        log.warning("Checksum error: return code =  "+str(rc)+" for file "+file)
                    else:
                        cksumout = foo.split()
                        cksums[cksumout[2]] = [cksumout[0],cksumout[1]]
                        pass
                else:
                    log.warning("Checksum error: file does not exist, "+file)
                    pass
                pass
            continue
# Print report, if requested
        if int(printflag) == 1:
            log.info("Checksum report")
            print "\n"
            for cksum in cksums:
                print "Checksum report for file: ",cksum," checksum=",cksums[cksum][0]," bytes=",cksums[cksum][1]
                pass
            print "\n"
            pass
        return cksums



    def getStageDir(self):
        """@brief Return the name of the stage directory being used"""
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
        log.info('\n\n\tStatus of File Staging System')
        log.info('setupFlag= '+str(self.setupFlag)+', setupOK= '+str(self.setupOK)+', stageDirectory= '+str(self.stageDir)+'\n')
        log.info(str(self.numIn)+" files being staged in")
        log.info(str(self.numOut)+" files being staged out")
        log.info(str(self.numMod)+" files being staged in/out for modification\n")

        # copy stageOut files to their final destinations
        for stagee in self.stagedFiles:
            stagee.dumpState()
            continue
        return

    def dumpFileList(self, mylist):
        """@brief Dummy for backward compatibility"""
        print "Entering dumpFileList (dummy method)"
        return




class StagedFile(object):

    def __init__(self, location, source=None, destinations=[],
                 cleanup=False, autoStart=True):
        self.source = source                   # (stageIn) original file location
        self.location = location               # temporary file location during job
        self.destinations = list(destinations) # (stageOut) list of final destinations for file
        self.cleanup = cleanup                 # cleanup=>remove file at finish()
        self.started = False                   # (stageIn) file has been copied to scratch area
        if location in self.destinations:      # prevent shooting self in foot
            self.destinations.remove(location)
            self.cleanup = False
            pass
        if autoStart:                          # cause files to be stagedIn
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

    def start(self):                   # copy stagedIn file to temporary working area
        self.dumpState()
        rc = 0
        if self.source and self.location != self.source and not self.started:
            rc = copy(self.source, self.location)
            pass
        self.started = True
        return rc

    def finish(self, keep=False):      # copy stagedOut file to final destination(s) & cleanup
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
xrootdLocation = os.getenv("GPL_XROOTD_DIR","/afs/slac.stanford.edu/g/glast/applications/xrootd/PROD/bin")
xrdcp = xrootdLocation+"/xrdcp "
xrdstat = xrootdLocation+"/xrd.pl -w stat "

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
    maxtry = 5
    mytry = 1
    rc = 0

    
# Verify source file is accessible
    if fromFile.startswith(xrootStart):
        xrdcmd=xrdstat+fromFile
        log.info("Verifying existence of "+fromFile)
        rc = os.system(xrdcmd)
        log.debug("xrdstat return code = "+str(rc))
        if int(rc) != 0:
            log.error("Could not access requested file: "+str(fromFile))
            return 1
        pass
    else:
        if not os.access(fromFile,os.R_OK):
            log.error("Could not access requested file: "+str(fromFile))
            return 1
        pass


# Copy source -> destination
    while mytry <= maxtry:
        if mytry > 1:        ## this happens during a retry
            log.warning("Retry xrdcp  (mytry = "+str(mytry)+") after a brief pause...")
            waitABit()       # spin wheels and hope things get better
            pass
        start = time.time()
        xrdcmd=xrdcp+" -np -f "+fromFile+" "+toFile   #first time try standard copy
        log.info("Try #"+str(mytry)+": executing...\n"+xrdcmd)
        rc = os.system(xrdcmd)
        log.debug("xrdcp return code = "+str(rc))
        if int(rc) != 0:
            rc = 0
            mytry += 1
            continue
        else:
            deltaT = time.time() - start
            log.info('Transferred file in %g seconds' %
                     (deltaT))
            break
        pass
    else:
        log.error("xrdcp repeatedly failed, setting rc=1")
        rc=1
        return rc
        pass
    
## Verify destination file has been copied
##   (this is a trivial existence check - more could be done here...)
    if toFile.startswith(xrootStart):
        xrdcmd=xrdstat+toFile
        log.info("Verifying existence of "+toFile)
        rc = os.system(xrdcmd)
        log.debug("xrdstat return code = "+str(rc))
        if int(rc) != 0:
            log.error("Could not access requested file: "+str(toFile))
            return 1
        pass
    else:
        if not os.access(toFile,os.R_OK):
            log.error("Could not access requested file: "+str(toFile))
            return 1
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

    tempName = toFile + '.part'

## To allow for possible filesystem failures (e.g. delay to
## automount), several attempts are made to copy the input file to
## local scratch space.  If that fails, then staging is effectively
## disabled for that file.
    log.debug("Looking for "+str(fromFile))
    if os.access(fromFile,os.R_OK):
        while mytry < maxtry:
            start = time.time()

            try:
                log.info('Starting try %d.' % mytry)
                rc |= mkdirFor(tempName)
                log.info("Copying %s to %s " % (fromFile, tempName))
                shutil.copy(fromFile, tempName)
                log.info("Renaming %s to %s" % (tempName, toFile))
                os.rename(tempName, toFile)
                rc = 0
                break
            except: # FIX THIS unconditional except makes debugging hard
                log.error("Error copying file to %s (try %d)" %
                          (toFile, mytry))
                waitABit()
                mytry = mytry + 1
                if mytry == maxtry: rc=1
                continue
            continue
        log.info('Succeeded after %d tries' % mytry)

        deltaT = time.time() - start
        try:
            size = os.stat(toFile).st_size
        except:
            size = 0
            deltaT = 0
            pass
        if deltaT:
            rate = '%g' % (float(size) / deltaT)
        else:
            rate = 'many'
            pass
        log.info('Transferred %g bytes in %g seconds, avg. rate = %s B/s' %
                 (size, deltaT, rate))
        return rc
    else:
        log.error("Unable to access "+str(fromFile))
        return 1
    pass



def mkdirFor(filePath):
    status = 0
    dirPath = os.path.dirname(filePath)
    if not os.path.isdir(dirPath):
        log.info('Making directory %s' % dirPath)
        status |= runner.run('mkdir -p %s' % dirPath)
        pass
    return status
