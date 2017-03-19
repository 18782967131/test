import logging
import sys
#CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
def log_dec(level):
	def inner(func):
		def inner1(str):
			#创建logger
			logger1 = logging.getLogger(sys.argv[0][:-3])
			logger1.setLevel(logging.DEBUG) 
			#创建输出到文件的logger
			logfile='log.txt'
			fh = logging.FileHandler(logfile, mode='a+')  
			fh.setLevel(logging.DEBUG)
			#创建输出到cmd的logger
			ch = logging.StreamHandler()  
			ch.setLevel(logging.WARNING)
			#定义输出格式
			formatter = logging.Formatter("[{level}] %(asctime)s - [%(name)s]: %(message)s".format(level=level))  
			fh.setFormatter(formatter)  
			ch.setFormatter(formatter)
			#添加logger
			logger1.addHandler(fh)  
			logger1.addHandler(ch)
			if level=='INFO':
				logger1.error(str)
			else:
				logger1.info(str)
			#每次执行完需要移除hander,否则输出重复log
			logger1.removeHandler(fh)
			logger1.removeHandler(ch)
		return inner1
	return inner
@log_dec('INFO')
def info(str):
	pass
@log_dec('DEBUG')
def debug(str):
	pass 
@log_dec('WARNING')
def warning(str): 
	pass
@log_dec('ERROR')
def error(str):
	pass
@log_dec('CRITICAL')
def critical(str):
	pass