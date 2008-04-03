#! /afs/slac/g/glast/isoc/flightOps/rhel3_gcc32/ISOC_PROD/bin/shisoc python2.5
## toXrootdCatalog.py - copy specified file to xrootd location and register in
##                      the data catalogue
##
## Sytnax:
##
## toXrootdCatalog.py -i <in_filespec> -x <xrootd path> -d <catalogue path>
##                       -t <in_fileType> -e <yes/no> -m 'metadata'
##                           -g <datacat_group_name>
##
## help:
##
## toXrootdCatalog.py -h
##
## R.Dubois  03 Apr 2008
##
##  Example:
##
##  copy pruned allGamma file to xrootd skims/ location and register in
##  the data catalogue, also in a skims/ folder of the allGamma task. It
##  is put into a group "pruneGamma" and tagged with metadata representing the
##  TCut applied in the prune.
##
##  If no cut is applied, there is no need to supply the -m option, and the
##  group would be "Concat"
##
##   noric11:richard> toXrootdCatalog.py -i $u18/MC-tasks/allGamma-GR-v13r9p12-LowE/prune5000/allGamma-GR-v13r9p12-LowE-pruned-merit.root -x mc/ServiceChallenge/allGamma-GR-v13r9p12-LowE/skims/ -d /MC-Tasks/ServiceChallenge/allGamma-GR-v13r9p12-LowE/skims/ -g pruneGamma -m 'TCut=ObfGamStatus>0'
##  
##
## References:
##
## xrootd client tools: https://confluence.slac.stanford.edu/display/ds/Using+Xrootd+client+tools
## datacat tools: https://confluence.slac.stanford.edu/display/ds/Data+Catalog+Users+Guide
##
## Some alternate installations of python for !shbang usage below...
##!/afs/slac/g/glast/isoc/flightOps/ISOC_PROD/bin/shisoc python2.5
##!/usr/local/bin/python


##
## Preliminaries
##
import os
import sys
import math
import stat
from optparse import OptionParser



print "\n\n\n\n\n\t\t*****************************\n\t\t* Entering toXrootdCatalog.py *\n\t\t*****************************\n\n"
sys.stdout.flush()


##
## Define command line arguments
##
parser = OptionParser(version="%prog $Revision 0.1",
         description="Copy file into xrootd and register in data catalogue")
parser.add_option("-i","--inputfile",action="store",type="string",dest="input",
                  help="Filespec of input file")
parser.add_option("-t","--inputfileType",action="store",type="string",dest="inputType",
                  default="merit",help="Datacat type of input file")
parser.add_option("-x","--xrootdpath",action="store",type="string",dest="xrootd",
                  help="directory path in xrootd, relative to top glast directory")
parser.add_option("-d","--datacatpath",action="store",type="string",dest="datacat",                  help="directory path in data catalogue")
parser.add_option("-e","--execute",action="store",type="string",dest="execute",                  default="no",help="really execute the commands if yes")
parser.add_option("-m","--metadata",action="store",type="string",dest="metadata",                  default="null",help="apply metadata to the dataset")
parser.add_option("-g","--group",action="store",type="string",dest="group",                  help="group in datacat")

(options, args) = parser.parse_args()

##
## interpret the input args & set up some defaults
##

inputFile = options.input
inputFileType = options.inputType
inputFileName = os.path.basename(inputFile)
xrootPath = options.xrootd
datacatPath = options.datacat
metaData = options.metadata
group = options.group

executeThis = options.execute

xrootRedirector = 'root://glast-rdr.slac.stanford.edu//glast/'
xrdcpLoc = '/afs/slac/g/glast/applications/xrootd/PROD/bin/xrdcp '

##
## Check existence of the input file

if int(os.access(inputFile,os.R_OK)) != 1:
    print 'Failed to access file '+inputFile
    exit(1)


## copy the file to xrootd


xrootFilePath = xrootRedirector + xrootPath + '/' + inputFileName
cmdXrootd = xrdcpLoc + ' -f ' + inputFile + ' ' + xrootFilePath

if executeThis == 'yes':
    fd = os.popen(cmdXrootd);
    foo = fd.read()
    rc = fd.close()
##    print 'Machine info:\n'+foo+'\n'
    if rc != None:
        print 'xrootd is not happy! Contact wilko@slac.stanford.edu\n'
        exit(1)
else:
    print 'Test prep of xrootd copy: ' + cmdXrootd

## register the file in the catalogue

datacatLoc = '/afs/slac.stanford.edu/g/glast/ground/bin/datacat '
useMeta = ''
if metaData != 'null': 
    useMeta = '"' + metaData + '"'
    
cmdDatacat = datacatLoc + 'registerDataset -G  ' + group + ' -D s' + useMeta + ' -S SLAC_XROOT ' + inputFileType + ' ' + datacatPath + ' ' + xrootFilePath

if executeThis == 'yes':
    fd = os.popen(cmdDatacat)    # register the file in the data catalogue
    foo = fd.read()
    rc = fd.close()
##    print 'Machine info:\n'+foo+'\n'
##    print rc
    if rc != None:
        print ' data catalogue registration is not happy! Contact dflath@slac.stanford.edu\n'
        exit(2)
else:
    print 'Test prep of datacat registration: ' + cmdDatacat

    
