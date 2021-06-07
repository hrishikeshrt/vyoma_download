#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 07 15:56:56 2021

@author: Hrishikesh Terdalkar
"""

import logging

###############################################################################

VERBOSE = 15
"""
The numeric value of the 'verbose' log level (a number).
The value of :data:`VERBOSE` positions the verbose log level between the
:data:`~logging.INFO` and :data:`~logging.DEBUG` levels.
:see also: The :func:`~VerboseLogger.verbose()` method of the
           :class:`VerboseLogger` class.
"""

NOTICE = 25
"""
The numeric value of the 'notice' log level (a number).
The value of :data:`NOTICE` positions the notice log level between the
:data:`~logging.WARNING` and :data:`~logging.INFO` levels.
:see also: The :func:`~VerboseLogger.notice()` method of the
           :class:`VerboseLogger` class.
"""

###############################################################################


class VerboseLogger(logging.Logger):

    """
    Custom logger class to support the additional logging levels.
    This subclass of :class:`logging.Logger` adds support for the additional
    logging methods :func:`notice()`, :func:`spam()`, :func:`success()` and
    :func:`verbose()`.
    You can use :func:`verbose_logger.install()` to make :class:`VerboseLogger`
    the default logger class.
    """

    def __init__(self, *args, **kw):
        """
        Initialize a :class:`VerboseLogger` object.
        :param args: Refer to the superclass (:class:`logging.Logger`).
        :param kw: Refer to the superclass (:class:`logging.Logger`).
        This method first initializes the superclass and then it sets the root
        logger as the parent of this logger.
        The function :func:`logging.getLogger()` is normally responsible for
        defining the hierarchy of logger objects however because verbose
        loggers can be created by calling the :class:`VerboseLogger`
        constructor, we're responsible for defining the parent relationship
        ourselves.
        """
        logging.Logger.__init__(self, *args, **kw)
        self.parent = logging.getLogger()

    def notice(self, msg, *args, **kw):
        """Log a message with level :data:`NOTICE`.
        The arguments are interpreted as for :func:`logging.debug()`."""
        if self.isEnabledFor(NOTICE):
            self._log(NOTICE, msg, args, **kw)

    def verbose(self, msg, *args, **kw):
        """Log a message with level :data:`VERBOSE`.
        The arguments are interpreted as for :func:`logging.debug()`."""
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kw)

###############################################################################


def add_log_level(value, name):
    """
    Add a new log level to the :mod:`logging` module.
    :param value: The log level's number (an integer).
    :param name: The name for the log level (a string).
    """
    logging.addLevelName(value, name)
    setattr(logging, name, value)


def install():
    """
    Make :class:`VerboseLogger` the default logger class.
    The :func:`install()` function uses :func:`~logging.setLoggerClass()` to
    configure :class:`VerboseLogger` as the default class for all loggers
    created by :func:`logging.getLogger()` after :func:`install()` has been
    called. Here's how it works:
    .. code-block:: python
        import logging
        import verbose_logger
        verbose_logger.install()
        logger = logging.getLogger(__name__) # will be a VerboseLogger instance
    """
    logging.setLoggerClass(VerboseLogger)


###############################################################################
# Define the custom log levels.

add_log_level(VERBOSE, 'VERBOSE')
add_log_level(NOTICE, 'NOTICE')
