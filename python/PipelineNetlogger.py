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


## @namespace PipelineNetlogger
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
#  # Pulling out all the stops:
#  log.fatal('logging.test', 'Arrrrrrrrrgggghhhhh!', link='Missing', tgt='Not WalMart',
#            scid=23, timestamp=log.lattime(secs,usecs),
#            tag_popeye=1, tag_olive=2, tag_j_wellington_wimpy=3)
#
#  # From now on only ERROR and FATAL messages will get logged.
#  log.setLevel("ERROR")
#  @endverbatim
#
#  For the detailed API see the documentation for class PNetlogger.

import datetime, getpass, md5, os, random, re, socket, sys, time, urlparse

from PipelineNetloggerConfig import DEST, LEVEL


def _metalog(level):
    # Return a logging function for a given severity level.
    # level is one of 'DEBUG', 'INFO', 'WARN', 'ERROR', or 'FATAL'.

    # Since the logging methods of the PNetlogger class all follow the
    # same pattern we'll use this function to generate them. The only
    # difference between the methods is the severity level.

    # Besides the standard arguments "evnt", "msg", "tgt",
    # "timestamp", "scid", and "link" each logging method will accept
    # an arbitrary number of keyword arguments whose keywords begin
    # with "tag_" and which accept integer values.  These extra
    # arguments will go into the dictionary passed to the log message
    # formatter.

    def log(self, evnt, msg, tgt="", timestamp=None, scid=-1, link="", **kwargs):
        # Start the dictionary of log message items with all the "tag_"
        # keyword items.
        items = dict((k, v) for k, v in kwargs.iteritems() if k.startswith("tag_"))
        # Were there any non-standard keyword args not starting with "tag_"?
        if len(items) != len(kwargs):
            raise TypeError("Invalid keyword arguments for logging: %s" %
                           ", ".join(set(kwargs) - set(items)))
        # Do all tags have integer values?
        bad = set(k for k, v in items.iteritems() if type(v) not in (int, long))
        if bad:
            raise ValueError("Tags don't have integer values: %s" % ", ".join(bad))
        # By convention Netlogger field names are upper case.
        items = dict((k.upper(), v) for k, v in items.iteritems())
        # Add the standard args to the items dict and call the formatting method.
        items.update(dict(MSG=msg,
                          TGT=tgt,
                          SCID=scid,
                          LINK=link,
                          LVL=level,
                          DATE=_dt.fromDatetime(timestamp)
                          )
                     )
        items.update(self._meta)
        msg = self._format(items)
        # Send the new message.
        self._appender.append(msg)

    return log


class PNetlogger(object):
    """!@brief Implements ISOC central logging for non-ISOC code.

    There are five logging methods named 'debug', 'info', 'warn',
    'error', and 'fatal'; each logs a message with the corresponding
    level of severity. Each takes the same type and number of
    arguments:

    log.<i>severity</i>(evnt, msg, tgt='', link = '', scid=-1, timestamp=None, **tags)
    - evnt --
    A string denoting the 'event type' for the message. This is
    normally a hierarchical form such as 'top.bottom',
    'top.middle.bottom', etc., where the bottom level serves as a sort
    of name for the message and the upper levels give context, e.g.,
    'tlm.rt.lat.alert' for telemetry processing, real-time, LAT alert
    processing. The LogWatcher web app can show you the list of event
    types already in use, which you should avoid in your own code.

    - msg --
    A string containing the text of the message.

    - tgt --
    A 'target' string whose meaning is determined by the user.

    - link --
    An application-depenedent field each containing pieces of a URL.

    - scid --
    Integer spacecraft ID, e.g., 77 for the real LAT. Normally you
    would give this argument only when logging a message concerning
    raw telemetry.

    - timestamp --
    A timestamp (in UTC) such as returned by the Python library
    function datetime.datetime(). Used to set the TEVNT column of a
    messages's database entry. A value of None will be replaced by the
    time at which the logging function was called. Use lattime() if
    you need to produce a suitable timestamp from CCSDS packet header
    information.

    - tags --
    A series of keyword arguments of the form 'tag_X=value' where X stands for
    a legal python name of at most 32 characters. The value given
    to a tag argument must be an integer. The pair (X.upper(), value) will be
    associated with the log message's entry in the database.
    """

    # Seconds between POSIX epoch and LAT epoch (2001-01-01 00:00:00)
    _LAT_EPOCH = datetime.datetime(2001, 1, 1, 0, 0, 0)

    @classmethod
    def lattime(cls, secs, usecs):
        """!@brief Converts CCSDS TIME44 secs and usecs to a UTC datetime.datetime.
        @param[in] secs The seconds field from a CCSDS timestamp.
        @param[in] usecs The microseconds
        """
        return cls._LAT_EPOCH + datetime.timedelta(seconds=secs, microseconds=usecs)

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
        # We'll use our NetlogdAppender to send the message strings
        # to the netlogd.
        self._appender = _NetlogdAppender(netlogDest)

        # Set the logging level.
        self._levelNames = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
        self._logLevel = None
        self.setLevel(netlogLevel)

        # Add metadata that is part of all messages.
        self._meta = { 'HOST' : socket.gethostname(),
                       'USER' : getpass.getuser(),
                       'PROG' : sys.argv[0],
                       'PID'  : os.getpid(),
                       'GID'  : _uuid(),
                       }

    def setLevel(self, netlogLevel):
        """!@brief Set the level threshold.
        @param[in] netlogLevel Messages less severe than this won't be
        logged. One of 'DEBUG', 'INFO', 'WARN', 'ERROR', or 'FATAL'.
        """
        try:
            self._loglevel = self._levelNames.index(netlogLevel.upper())
        except ValueError:
            raise ValueError("'%s' is not a valid level name." % netlogLevel)

    # The logging method for each severity level is generated by the _metalog function.
    fatal = _metalog("FATAL")

    error = _metalog("ERROR")

    warn = _metalog("WARN")

    info = _metalog("INFO")

    debug = _metalog("DEBUG")

    def _format(self, items):
        level = self._levelNames.index(items['LVL'].upper())
        if level < self._logLevel:
            return None
        return ''.join(list(_dictToText(items)))




class _NetlogdAppender(object):
    # Send messages to all netlogds one at a time, making the connection
    # for each message.
    def __init__(self, netlogDest):
        # Store the set of tuples (IP addr, port).
        self._destinations = list(_parseNetlogDest(netlogDest))
        pass

    def append(self, msg):
        if msg is None:
            # The original message didn't pass the severity level filter.
            return
        # Try each destination in turn.
        sent = False
        for dest in self._destinations:
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


def _dictToText(d):
    # A generator that yields text lines (with newlines)
    # given a message a dictionary form.
    for k, v in d.iteritems():
        k = _filterKey(k)
        t, v = _filterValue(v)
        yield "%s %s: %s\n" % (t, k, v)
    yield "\n"


def _filterKey(k):
    # Return the given key if it's valid, else raise _BadKey.
    if _BAD_KEY_CHARS.search(k):
        raise _BadKey(k)
    return k

## Delimiter characters that can't appear in keys: space, tab, colon.
_BAD_KEY_CHARS = re.compile(r"[ 	:]")


class _BadKey(Exception):
    # Raised if a key contains illegal characters.
    pass


class _dt(datetime.datetime):
    # Like datetime but str() separates date from time with 'T'.
    def __str__(self):
        return self.isoformat()

    @classmethod
    def fromDatetime(cls, dt=None):
        if dt is None:
            dt = datetime.datetime.utcnow()
        return _dt(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)


# Associate data types with type letters.
_TYPE_LETTER = {int:   "i",
               long:  "i",
               str:   "s",
               float: "f",
               _dt: "t"
               }

def _filterValue(v):
    # Returns (type letter, _cleanText(str(v))) given a
    # dictionary value v.
    try:
        t = _TYPE_LETTER[type(v)]
    except KeyError:
        t = "s"
    return t, _cleanText(str(v))


class _Transmogrifier(object):
    # Implement multiple string replacements in parallel during a single
    # pass of the original string. Replacement strings are not themselves
    # examined for possible replacements.

    # A giant regular expression is made where each key in the
    # dictionary repdict given to the constructor is an
    # alternative. Then the original string is searched and when a match
    # is found the alternative X that matched is replaced by
    # repdict[X]. Any characters meaningful in regular expressions are
    # escaped in each alternative, so any string can be searched for.
    def __init__(self, repdict):
        # Store the dictionary of replacements and make up the
        # regular expression.

        # repdict is a dictionary of replacements. If X in repdict
        # then we'll replace X with repdict[X].
        self.repdict = dict(repdict)
        self.rx = self._makeRx()

    def _makeRx(self):
        # Return the compiled regular expression made from the
        # dictionary given to the constructor.
        return re.compile("|".join([re.escape(x) for x in self.repdict]))

    def _oneInstance(self, match):
        # Called by the sub() method of self.rx to return the
        # replacement string corresponding to a given matched substring.
        return self.repdict[match.group(0)]

    def __call__(self, text):
        # Return the argument string transmogrified.
        return self.rx.sub(self._oneInstance, text)


class _IsocTransmogrifier(_Transmogrifier):
    # Transform arbitrary strings into ones acceptable in
    # ISOC logger message lines after the type letter and keyword.

    # Remove all non-printing characters except newline and tab. Replace
    # newline with ' -NL- ', and truncate after those transformations to
    # MAXLEN characters.

    # The transformed string will be truncated at this size.
    MAXLEN = 4000

    def __init__(self):
        # Replace by a null string each eight-bit character.
        repdict = dict(  (chr(x), "") for x in xrange(128, 256))
        # Replace by null strings all control characters except space, tab, and newline.
        repdict.update( dict((chr(x), "")
                             for x in xrange(0, 26)
                             if x not in (ord(" "), ord("\t"), ord("\n"))) )
        # Change newline to " -NL- ".
        repdict["\n"] = " -NL- "
        super(_IsocTransmogrifier, self).__init__(repdict)

    def __call__(self, text):
        # Truncate after transmogrification.
        return super(_IsocTransmogrifier, self).__call__(text)[0:self.MAXLEN]

# Apply an _IsocTransmogrifier to a string.
_cleanText = _IsocTransmogrifier()

# From: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761
def _uuid( *args ):
  # Generates a universally unique ID.
  # Any arguments only create more randomness.
  t = long( time.time() * 1000 )
  r = long( random.random()*100000000000000000L )
  try:
    a = socket.gethostbyname( socket.gethostname() )
  except:
    # if we can't get a network address, just imagine one
    a = random.random()*100000000000000000L
  data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
  data = md5.md5(data).hexdigest()
  return data
