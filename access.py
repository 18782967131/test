#coding:utf-8
import paramiko
import time
import logger
class ssh():
	def __init__(self,username,password,ip,port):
		self.username=username
		self.password=password
		self.ip=ip
		self.port=port
		self.state=False
		self.try_time=0
		self.chan=''
	def connect(self):
		self.client=paramiko.SSHClient()
		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		logger.info('connect linux')
		logger.debug('logging debug test')
		logger.debug('logging debug test2')
		while not self.state:
			try:
				self.client.connect(self.ip,self.port,self.username,self.password)
				self.state=True
			except:
				self.try_time+=1
				if self.try_time==3:
					print('try {time} to connect {ip} fail!'.format(time=self.try_time,ip=self.ip))
					break
				else:
					print('try {time} to connect {ip} fail! and retry to connect'.format(time=self.try_time,ip=self.ip))
		if self.state:
			self.chan=self.client.invoke_shell()
	def read_all(self):
		buff=self.chan.recv(1024)
		rec+=buff
		while len(buff)==1024:
			buff=self.chan.recv(1024)
			rec+=buff
		return rec
	def ex_cmd(self,cmd,root=False):
		#sudo需要在exec_command添加参数get_pty=True
		if root:
			get_pty=True
		else:
			get_pty=False
		stdin,stdout,stderr=self.client.exec_command(cmd,get_pty=True)
		if root:
			stdin.write('{root}\r\n'.format(root=root))
			stdin.flush()
		err=stderr.read()
		if err:
			return err
		return stdout.read()