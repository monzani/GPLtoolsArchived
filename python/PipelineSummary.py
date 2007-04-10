#! /afs/slac/g/glast/isoc/flightOps/rhel4_gcc32/ISOC_PROD/bin/shisoc python2.5
##
## Preliminaries
##

from GPL import *

class PipelineSummary():
    """
    @brief Create and write user-generated summary data for pipeline DB

    Example:
    mySummary = PipelineSummary.PipelineSummary("pipeline_summary")
    mySummary.add("EventsProcessed","41669")
    mySummary.add("TimeElapsed","493829746")
    mySummary.add("TimeInSAA","89334")
    mySummary.write()

    This will append the following lines to the specified file:

Pipeline.EventsProcessed: 41669
Pipeline.TimeElapsed: 493829746
Pipeline.TimeInSAA: 89334

    These data will then be processed by the Pipeline server and entered into its database.

    Note that one may optionally specify a "prefix" as the second argument to the constructor
    which defaults to "Pipeline.", suitable for the Pipeline 2 summary file, but can also
    be set to null for other applications.

    @todo proper error checking on summary file (pre-existence, success of write, etc.)

    @author T.Glanzman <dragon@slac.stanford.edu>

    3/21/2007
    """

# Constructor (specifies name of summary file)
    def __init__(self, filename="./pipeline_summary", prefix="Pipeline."):
        self.itemList = []
        self.numItems = 0
        self.prefix = prefix
        self.filename = filename
        log.debug('PipelineSummary constructor, filename = '+self.filename)
        return

# Main entry to add new summary datum
    def add(self,key,value):
#        log.debug('entering add(), key= '+key+', value= '+value)
        self.numItems = self.numItems+1
        self.itemList.append(self.prefix+key+': '+value+"\n")
        return

# Debugging dump of internal list of summary data
    def dump(self):
        print 'Dump of current user summary data:'
        print "Summary filename = ",self.filename
        print "Summary item prefix = ",self.prefix
        print "There are ",self.numItems," items in the Summary list."
#        print self.itemList
        print "\n----------begin summary----------------------------------"
        for x in self.itemList:
            x = x.strip()
            print x
        print "----------end summary----------------------------------\n"


# Write assembled list of summary data to summary file
    def write(self):
        log.debug('entering PipelineSummary.write() to '+self.filename)

        log.debug('Number of items in list = '+str(self.numItems))
        self.summary = open(self.filename,'a')
        self.summary.writelines(self.itemList)
        self.summary.close()
        return
