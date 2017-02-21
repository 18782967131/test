import socketserver
import sys
host='0.0.0.0'
port=9000
client_list=[]
#重写handle处理数据
class MyTCPHandler(socketserver.BaseRequestHandler):
	#在handle之前调用，默认不做任何操作
	def setup(self):
		pass
		#print(self.client_address,'set up')
	#在handle之后调用，默认不做任何操作
	def finish(self):
		pass
		#print(self.client_address,'finish')
	def handle(self):
		global client_list
		self.conn = self.request
		client_list.append(self.conn)
		print(client_list)
		try:
			self.conn.sendall('i am threading:{client}'.format(client=self.client_address).encode('utf-8'))
			Flag = True
			while Flag:
				data = self.conn.recv(1024).decode('utf-8')
				print(data)
				if data == 'exit':
					Flag = False
				elif data == '0':
					self.conn.sendall('you are input 0'.encode('utf-8'))
				else:
					self.conn.sendall('please input....'.encode('utf-8'))
		except:
			if self.conn in client_list:
				client_list.remove(self.conn)
				#print('{client},leave by self!'.format(client=self.client_address).encode('utf-8'))
			else:
				#self.conn.sendall('{client},disconnect by server!'.format(client=self.client_address).encode('utf-8'))
				pass
if __name__=='__main__':
	server = socketserver.ThreadingTCPServer((host,port), MyTCPHandler)
	try:
		server.serve_forever()
	except:
		for x in client_list:
			client_list.remove(x)
			x.close()
		server.shutdown()
		server.server_close()