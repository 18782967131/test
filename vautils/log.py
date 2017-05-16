"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

log implements custom functions that wrap around the functionality
exposed by the built in module logging

.. moduleauthor:: ppenumarthy@varmour.com
"""

import os
import logging

from time import gmtime, strftime

log_id = strftime("%H:%M:%S", gmtime()).replace(':','')


def va_fwk_log(name=None, console=True, logfile=None):
    """
    function to configure logger, handler, and formatter. This will log
    to the console

    Args:
        :name (str): name of the module that is logging

    Returns:
        an instance of the builtin logging.getLogger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    logformat = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
    )

    console_log, file_log = None, None

    if console:
        console_log = logging.StreamHandler()
    
    if not logfile:
        logname = ''.join(('vatf_fwk', '_', log_id, '.', 'log'))
        #print("from log: ", os.getcwd())
        logfile = os.path.join(os.getcwd(), logname)        

    file_log = logging.FileHandler(filename=logfile, mode='a')

    for logger_type in console_log, file_log:
        if logger_type:
            logger_type.setLevel(logging.DEBUG)
            logger_type.setFormatter(logformat)
            logger.addHandler(logger_type)

    return logger


def va_log_console(name):
    """
    function to configure logger, handler, and formatter. This will log
    to the console

    Args:
        :name (str): name of the module that is logging

    Returns:
        an instance of the builtin logging.getLogger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s'
    )

    console.setFormatter(formatter)

    logger.addHandler(console)

    return logger
