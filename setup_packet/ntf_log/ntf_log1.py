import os
import logging

from time import gmtime, strftime

log_id = strftime("%H:%M:%S", gmtime()).replace(':','')

def ntf_fw_log(name=None, console=True, logfile=None):
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
        console_log.setLevel(logging.INFO)

    if not logfile:
        logname = ''.join(('ntf', '_', log_id, '.', 'log'))
        logfile = os.path.join(os.getcwd(), logname)        

    file_log = logging.FileHandler(filename=logfile, mode='a')
    file_log.setLevel(logging.DEBUG)
    for logger_type in console_log, file_log:
        if logger_type:
            logger_type.setFormatter(logformat)
            logger.addHandler(logger_type)

    return logger