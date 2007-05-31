#  stageFiles.py
"""@brief Manage staging of files to/from machine-local disk.
$Id$
@author W. Focke <focke@slac.stanford.edu>

refactored: T.Glanzman 2/22/2007
"""

## Preliminaries
import os
import sys
import shutil

## Set up message logging
import logging
log = logging.getLogger("gplLong")

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


    def __init__(self, stageName=None, stageArea=None):
        """@brief Initialize the staging system
        @param [stageName] Name of directory where staged copies are kept.
        @param [stageArea] Parent of directory where staged copies are kept.
        """

        log.debug("Entering stageFiles constructor...")
        self.setupFlag = 0
        self.setupOK = 0
        
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
        self.inFiles = {}
        self.outFiles = {}
        self.realInFiles = {}
        self.realOutFiles = {}
        self.realOutFiles2 = {}
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
            log.warning("stageIn not available for: "+inFile)
            return inFile
        
## To allow for possible filesystem failures (e.g. delay to
## automount), several attempts are made to copy the input file to
## local scratch space.  If that fails, then staging is effectively
## disabled for that file.

        log.info("stageIn for: "+inFile)
        maxtry = 30
        mytry = 1
        while mytry < maxtry:
            try:
                stageName = self.stagedName(inFile)
                shutil.copy(inFile, stageName)
                self.numIn=self.numIn+1
                self.realInFiles[self.numIn]=inFile
                self.inFiles[inFile] = stageName
                break
#            except OSError:
            except:
                log.warning('Error copying from '+inFile+' (try '+`mytry`+')')
                os.system("sleep 2")
                self.inFiles[inFile] = ""
                stageName = inFile
                mytry = mytry+1

        return stageName

    
    def stageOut(self, outFile, outFile2=""):
        """@brief Stage an output file.
        @param outFile  = real name of the primary output file
               outFile2 = real name of the secondary output file (e.g. xrootd)
        @return name of the staged file
        """
        if self.setupFlag <> 1: setup()
        if self.setupOK <> 1:
            log.warning("stageOut not available for: "+outFile)
            return outFile
        
        log.info("stageOut for: "+outFile)
        if outFile == "":
            log.error("primary stage file not specified")
            return ""
        stageName = self.stagedName(outFile)
        self.numOut=self.numOut+1
        self.realOutFiles[self.numOut]=outFile
        self.realOutFiles2[self.numOut]=outFile2
        self.outFiles[outFile] = stageName

        return stageName


    def finish(self,option=""):
        """@brief Delete staged inputs, move outputs to final destination.
        option: additional functions
        keep    - no additional function (in anticipation of further file use)
        clean   - +move/delete all staged files (in anticipation of further directory use)
        <null>  - +remove stage directories (full cleanup)
        """
        log.debug('Entering stage.finish('+option+')')
        rc = 0     # overall
        rcf = 0    # standard file copy
        rcx = 0    # xrootd copy
        rce = 0    # file existence 
        
        ## bail out if no staging was done
        if self.setupOK == 0: return rc
        log.debug("*******************************************")

        # copy stageOut files to their final destinations
        for item in self.realOutFiles.items():
            index = item[0]
            realName = item[1]
            realName2 = self.realOutFiles2[index]
            stageName = self.outFiles[realName]
##            print "\n**TEST: index = ",index,", stageName = ",stageName,\
##                  "\n\t>> realName= ",realName,", realName2 = ",realName2
            if os.access(stageName,os.R_OK):    # Check output file really exists before copying

            # Primary stageOut file
                # xrootd file
                if realName[0:5] == "root:":
                    x = self.xrootdCopy(stageName,realName)
                    rcx += x
                    log.debug("ReturnCode from xrootdCopy() = "+str(x))

                # Ordinary disk file
                else:
                    s = self.fileCopy(stageName,realName)
                    rcf += s
                    log.debug("ReturnCode from fileCopy() = "+str(s))

             # Secondary stageOut file [optional]     
                if realName2 == "":     # check if 2nd output location is specified
                    continue
                else:
                    # xrootd file
                    if realName2[0:5] == "root:":
                        x = self.xrootdCopy(stageName,realName2)
                        rcx += x
                        log.debug("ReturnCode from xrootdCopy() = "+str(x))
                    # Ordinary disk file
                    else:
                        s = self.fileCopy(stageName,realName2)
                        rcf += s
                        log.debug("ReturnCode from fileCopy() = "+str(s))
            else:
                log.error('Expected output file does not exist! '+stageName)
                rce += 1

        ## Define return code as sum of relevant errors
        if self.xrootdIgnoreErrors == True:
            rc = rcf + rce
        else:
            rc = rcf + rcx + rce
            
        if option == "keep": return rc              # Early return #1

        # remove stageIn files from staging directory
        for stageName in self.inFiles.values():
            if os.access(stageName,os.W_OK): os.remove(stageName)

        # remove stageOut file from staging directory
        for stageName in self.outFiles.values():
            if os.access(stageName,os.W_OK):
                os.remove(stageName)  # remove stageOut files
            else:
                log.warning("Could not access/remove from stage directory: "+stageName)

        # Initialize stage data structures
        self.reset()

        if option == "clean": return rc           # Early return #2
                            

        # remove stage directory
        try:
            os.rmdir(self.stageDir)
        except:
            log.warning("Staging directory not empty after cleanup!!")
            log.warning("Content of staging directory "+self.stageDir)
            os.system('ls -l '+self.stageDir)
            log.warning("*** All files & directories will be deleted! ***")
            try:
                shutil.rmtree(self.stageDir)
            except:
                log.error("Could not remove stage directory, "+self.stageDir)
        self.setupFlag=0
        self.setupOK=0
        self.reset()
 
        return rc




    def xrootdCopy(self,fromFile,toFile):
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
        return rc



    

    def fileCopy(self,fromFile,toFile):
        """
        @brief copy a staged file to final disk location
        @param fromFile = name of staged file, toFile = name of final file
        @return success code
        """
        maxtry = 5
        mytry = 1
        rc=0
        while mytry < maxtry:
            try:
                log.info("Executing:\ncp "+fromFile+" "+toFile)
                shutil.copy(fromFile,toFile)
                break
            except:
                log.error("Error copying stageOut file to "+toFile+" (try "+`mytry`+")")
                os.system("sleep 2")
                mytry = mytry + 1
                if mytry == maxtry: rc=1
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
        return `self.setupOK`



    def dumpStagedFiles(self):
        """@brief Dump names of staged files to stdout"""
        print '\n\n\tStatus of File Staging System'
        print 'setupFlag= ',self.setupFlag,', setupOK= ',self.setupOK,', stageDirectory= ',self.stageDir,'\n'
        print self.numIn," files staged in:"
        ix=1
        while ix <= self.numIn:
            foo = self.realInFiles[ix]
            foo2 = self.inFiles.get(foo)
            print foo," --> ",foo2
            ix = ix + 1
            
        print self.numOut," files staged out:"
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
