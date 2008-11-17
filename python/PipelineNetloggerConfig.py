#
#                               Copyright 2007
#                                     by
#                        The Board of Trustees of the
#                     Leland Stanford Junior University.
#                            All rights reserved.
#

"""Default configuration parameters for ISOC loggers used in pipeline
batch jobs."""

__facility__ = "GLAST ISOC"
__abstract__ = __doc__
__author__   = "Stephen Tether <tether@slac.stanford.edu> SLAC - GLAST ISOC"
__date__     = "2007/09/12"
__updated__  = "$Date$"
__version__  = "$Revision$"
__release__  = "$Name$"
__credits__  = "SLAC"

# Production setup. Messages will show up in the Flight page of LogWatcher.
DEST_PROD  = "glastlnx06:15502 isoc-ops5:15502"
LEVEL_PROD = "INFO"

# Development. Messages will show the Test page.
DEST_DEVEL  = "glastlnx25:15502"
LEVEL_DEVEL = "INFO"
