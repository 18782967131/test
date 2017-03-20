import paramiko,time
class zdy_ssh():
    def __init__(self,ip,port,username,password):
        self.state=True
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(ip,port,username,password)
        except:
            self.state=False
        if self.state:
            self.s=self.ssh.invoke_shell()
    def ex_cmd(self,cmd):
        self.s.send(cmd+'\n')
    def expect_end(self,end):
        r=''
        while not r.endswith(end):
            r+=self.s.recv(1024)
        return r
    def check_end(self,end):
        r=s.recv(1024)
        while True:
            r1=self.s.recv(1024)
            if not r1:
                break
            r+=r1
        if r.endswith(end):
            return True
        else:
            return False
    def close(self):
        self.ssh.close()
'''aa=zdy_ssh('10.11.123.140',22,'varmour','vArmour12')
time.sleep(2)
aa.expect_end(' ')
print '++++'
'''
