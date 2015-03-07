# -*- coding: utf-8 -*-

import time
import os
from logorigins import logger


def os_query(qry):
    start = time.time()
    retval = os.system(qry)
    duration = time.time() - start
    if retval:
        logger.error("[%(duration).2fs], retval=%(retval)s, %(qry)s" % locals())
        raise OSError("Cannot execute %(qry)s" % locals())
    else:
        logger.info("[%(duration).2fs], retval=%(retval)s, %(qry)s" % locals())


def remove_and_create_directory(directory):
    os_query("rm -rf %(directory)s" % locals())
    os_query("mkdir -p %(directory)s" % locals())


def create_directory(directory):
    os_query("mkdir -p %(directory)s" % locals())


duration_suffixes = dict((
    ("s", 1),
    ("m", 60),
    ("h", 60 * 60),
    ("d", 24 * 60 * 60),
    ("w", 7 * 24 * 60 * 60),
    ("y", 365 * 7 * 24 * 60 * 60)
))


def parse_duration(duration):
    """
        Parse human duration into duration in seconds
    """
    if not isinstance(duration, str) and not isinstance(duration, unicode):
        raise TypeError("Cannot parse duration. Must be string or unicode")
    if duration.isdigit():
        return int(duration)
    suffix = duration[-1]
    prefix = duration[:-1]
    return int(prefix) * duration_suffixes[suffix]
