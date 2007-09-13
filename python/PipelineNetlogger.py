#
#                               Copyright 2007
#                                     by
#                        The Board of Trustees of the
#                     Leland Stanford Junior University.
#                            All rights reserved.
#

"""Provides pipeline batch jobs the ability to use the ISOC logging facility."""

__facility__ = "GLAST ISOC"
__abstract__ = __doc__
__author__   = "Stephen Tether <tether@slac.stanford.edu> SLAC - GLAST ISOC"
__date__     = "2007/09/12"
__updated__  = "$Date$"
__version__  = "$Revision$"
__release__  = "$Name$"
__credits__  = "SLAC"


## @file PipelineNetlogger.py
#  @brief Provides pipeline batch jobs with the ability use the
#  ISOC logging facility from Python.
#  @par Examples
#  @verbatim
#  import GPLinit
#  from GPL import PNetlogger
#  log = PNetlogger.getLogger()
#
#  # Default timestamp, no target or SCID. The normal case.
#  log.info("log.test", "Hello")
#
#  # Assume you've got a CCSDS telemetry packet from source 99 and
#  # you've extracted the seconds and microseconds fields from the
#  # secondary header. You want the log message TEVNT timestamp to be
#  # the same as the packet creation time (there is a separate
#  # timestamp showing when the log message was posted to the central
#  # database).
#  log.info("science.ccsds", "Got a packet.", scid = 99, timestamp = log.lattime(secs,usecs))
#
#  # From now on only ERROR and FATAL messages will get logged.
#  log.setLevel("ERROR")
#  @endverbatim

import getpass, os, random, re, socket, sys, urlparse

from lbl.dsd.netlogger import nllite

from PipelineNetloggerConfig import DEST, LEVEL

class PNetlogger(object):
    """!@brief Implements ISOC central logging via LBL's Netlogger."""

    # Seconds between POSIX epoch and LAT epoch (2001-01-01 00:00:00)
    _LAT_EPOCH = 978307200.0

    @classmethod
    def lattime(cls, secs, usecs):
        """!@brief Converts CCSDS TIME44 secs and usecs to a time.time()-like
        timestamp suitable for use with debug() <i>et al</i>.
        @param[in] secs The seconds field from a CCSDS timestamp.
        @param[in] usecs The microseconds
        """
        return secs + cls._LAT_EPOCH + usecs / 1.0e6

    # The instance initialized with standard parameters.
    _standardLogger = None

    @classmethod
    def getLogger(cls):
        """!@brief Return the standard logger instance (always the same one).

        There is an instance of PNetlogger available which has been
        initialized with default values for the logging server
        locations and for the severity level threshold.
        """
        if cls._standardLogger is None:
            cls._standardLogger = cls(DEST, LEVEL)
        return cls._standardLogger


    def __init__( self, netlogDest, netlogLevel):
        """!@brief Set up logging.
        """
        # Create a LogOutputStream with no associated file or URL.
        # We'll use it only for formatting and filtering against
        # severity level.
        self.__log = nllite.LogOutputStream(logfile = None)

        # We'll use our NetlogdAppender to send the message strings
        # to the netlogd.
        self.__appender = _NetlogdAppender(netlogDest)

        # Set the logging level.
        self.setLevel(netlogLevel)

        # Add metadata that is part of all messages.
        self.__meta = { 'HOST' : socket.gethostname(),
                        'USER' : getpass.getuser(),
                        'PROG' : nllite.get_prog(),
                        'PID'  : os.getpid(),
                        'GID'  : nllite.get_gid(),
                        }
        self.__log.setMeta( None, self.__meta )

    def setLevel(self, netlogLevel):
        """!@brief Set the level threshold.
        @param[in] netlogLevel Messages less severe than this won't be
        logged. One of 'DEBUG', 'INFO', 'WARN', 'ERROR', or 'FATAL'.
        """
        self.__loglevel = netlogLevel.upper()
        if not hasattr(nllite.Level, self.__loglevel):
            raise ValueError("'%s' is not a valid level name." % self.__loglevel)
        self.__log.setLevel(getattr(nllite.Level, self.__loglevel))

    def fatal( self, evnt, msg, tgt='', timestamp=None, scid=-1 ):
        """!@brief Log a message with level FATAL.
        @see debug() for a description of the arguments.
        """
        msg = self.__log.write( evnt,
                                { 'MSG' : msg, 'TGT' : tgt, 'SCID' : scid },
                                level = nllite.Level.FATAL,
                                timestamp=timestamp )
        self.__appender.append(msg)

    def error( self, evnt, msg, tgt='', timestamp=None, scid=-1 ):
        """!@brief Log a message with level ERROR.
        @see debug() for a description of the arguments.
        """
        msg = self.__log.write( evnt,
                                { 'MSG' : msg, 'TGT' : tgt, 'SCID' : scid },
                                level = nllite.Level.ERROR,
                                timestamp=timestamp )
        self.__appender.append(msg)

    def warn( self, evnt, msg, tgt='', timestamp=None, scid=-1 ):
        """!@brief Log a message with level WARN.
        @see debug() for a description of the arguments.
        """
        msg = self.__log.write( evnt,
                                { 'MSG' : msg, 'TGT' : tgt, 'SCID' : scid },
                                level = nllite.Level.WARN,
                                timestamp=timestamp )
        self.__appender.append(msg)

    def info( self, evnt, msg, tgt='', timestamp=None, scid=-1 ):
        """!@brief Log a message with level INFO.
        @see debug() for a description of the arguments.
        """
        msg = self.__log.write( evnt,
                                { 'MSG' : msg, 'TGT' : tgt, 'SCID' : scid },
                                level = nllite.Level.INFO,
                                timestamp=timestamp )
        self.__appender.append(msg)

    def debug( self, evnt, msg, tgt='', timestamp=None, scid=-1 ):
        """!@brief Log a message with level DEBUG.
        @param[in] evnt
        A string denoting the "event type" for the
        message. This is normally a hierarchical form such as
        "top.bottom", "top.middle.bottom", etc., where the bottom level
        serves as a sort of name for the message and the upper levels
        give context, e.g., "tlm.rt.lat.alert" for telemetry processing,
        real-time, LAT alert processing. The LogWatcher web app can show
        you the list of event types already in use, which you should
        avoid in your own code.

        @param[in] msg
        A string containing the text of the message.

        @param[in] tgt
        A "target" string whose meaning is determined by the user.

        @param[in] tevnt
        A floating-point timestamp such as returned by the
        Python library function time.time(). It contains a number of
        seconds (with fractional part) since the start of the Unix epoch,
        1970 Jan 1 00:00:00.0. Normally you omit the timestamp in which case
        the message "event time" is set to the time you called the
        logging method. If you need the message to be associated with the
        time of some external event then give an appropriate tevnt. The
        class method lattime() is provided to help
        construct timestamps.

        @param[in] scid
        Integer spacecraft ID, e.g., 77 for the real
        LAT. Normally you would give this argument only when logging a message
        concerning raw telemetry.
        """
        msg = self.__log.write( evnt,
                                { 'MSG' : msg, 'TGT' : tgt, 'SCID' : scid },
                                level = nllite.Level.DEBUG,
                                timestamp=timestamp )
        self.__appender.append(msg)




class _NetlogdAppender(object):
    # Send messages to all netlogds one at a time, making the connection
    # for each message.
    def __init__(self, netlogDest):
        # Store the set of tuples (IP addr, port).
        self.__destinations = list(_parseNetlogDest(netlogDest))

    def append(self, msg):
        if msg is None:
            # The original message didn't pass the severity level filter.
            return
        # Try each destination in turn.
        sent = False
        for dest in self.__destinations:
            # Create a socket with that does not delay sending small
            # pieces of data.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Attempt to connect to the destination.
            try:
                sock.connect(dest)
                # Send the message, close the socket
                sock.sendall(msg)
                sock.close()
                # Exit the loop over destinations.
                sent = True
            except socket.error:
                pass

        # If no connection was made dump the message to stderr.
        if not sent:
            print >>sys.stderr, "Couldn't send this ISOC log message to any server:"
            print msg



def _parseNetlogDest(netlogDest):
    # Generator of tuples (ip addr, port).
    # netlogDest is of the form "jobs(url-list) scripts(url-list)" or
    # just a URL list.  We want the URLs for jobs rather than scripts;
    # URLs without either "jobs" or "scripts" in front of them apply
    # to both.
    forJobs = True
    dests = [d for d in re.split(" +|\(|\)", netlogDest) if d != ""]
    for d in dests:
        if d.lower() == "jobs":
            forJobs = True
        elif d.lower() == "scripts":
            forJobs = False
        elif forJobs:
            if d.startswith("x-netlog:"):
                # urlparse does a bad job with non-standard URLs.
                # So replace 'x-netlog' with 'http'.
                url = urlparse.urlparse("http" + d[8:])
                if ":" in url[1]:
                    host, port = url[1].split(":")
                else:
                    raise ValueError("Netlogger URLs must include the port number.")
                yield (host, int(port))
            else:
                raise ValueError("Netlogger URLs must begin with 'x-netlog:'.")

