from vautils.log import va_fwk_log
try :
    logger = va_fwk_log(__name__,True,log_file)
except:
    logger = va_fwk_log(__name__)
