import test_log
#每个模块__init__调用一次 name显示为改模块名
logger=test_log.va_fwk_log(__name__, console=True, logfile='log.txt')