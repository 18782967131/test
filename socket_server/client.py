import socket
ip_port = ('127.0.0.1',9000)
sk = socket.socket()
sk.connect(ip_port)
while True:
	try:
		data = sk.recv(1024).decode('utf-8')
		print('receive:',data)
		inp = input('please input:')
		while not len(inp):
			inp = input('please input:')
		sk.sendall(inp.encode('utf-8'))
		if inp == 'exit':
			break
	except:
		break
sk.close()