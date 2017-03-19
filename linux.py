import access
pc1=access.ssh('admin','admin','192.168.1.114',22)
pc1.connect()
print(pc1.ex_cmd('ifconfig eth0'))