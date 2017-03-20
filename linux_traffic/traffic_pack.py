import paramiko,time,os,re
class get_ssh():
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
            self.s.send('rm -f nohup.out'+'\n')
    def get_pid(self,name):
        self.s.send('ps -aux|grep {name}'.format(name=name)+'\n')
        time.sleep(1)
        r=self.s.recv(1024)
        pid_l=[]
        for x in r.split('\n'):
            if x.startswith('root'):
                for i in x.split(' '):
                    if i.isdigit():
                        pid_l.append(int(i))
                        break
		if pid_l:
			pid_l.pop()
        return pid_l
    def ex_cmd(self,cmd):
        self.s.send(cmd+'\n')
    def expect_end(self,end):
        r=''
        while not r.endswith(end):
            r+=self.s.recv(1024)
        return r
    def read_all(self):
        r1=''
        r=self.s.recv(1024)
        r1=r1+r
        while len(r)==1024:
            r=self.s.recv(1024)
            r1=r1+r
        return r1 
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
class ICMP():
    def __init__(self,server,source,dest,intf='eth0',count=0,length=64):
        self._src=source
        self._dest=dest
        self._count=count
        self._intf=intf
        self._length=length
        self._server=server             #get_ssh(self._src,22,'root','asd123456')
        self._icmp_str1='PING {dest} ({dest}) from {src} {intf}: {length1}({length2}) bytes of \
data.'.format(dest=self._dest,src=self._src,intf=self._intf,length1=self._length,length2=self._length+28)
        self._icmp_str2='--- {dest} ping statistics ---'.format(dest=self._dest)
    def start(self):
        if self._count:
            cmd='nohup ping {dest} -I {intf} -c {count} -s {length} &'.format(dest=self._dest,\
        intf=self._intf,count=self._count,length=self._length)
        else:
            cmd='nohup ping {dest} -I {intf}  -s {length} &'.format(dest=self._dest,\
        intf=self._intf,length=self._length)
        pid1_l=self._server.get_pid('ping')
        self._server.ex_cmd(cmd)
        pid2_l=self._server.get_pid('ping')
        for x in pid2_l:
            if x not in pid1_l:
                return x
    def stop(self,pid):
        cmd='kill -9 {pid}'.format(pid=pid)
        self._server.ex_cmd(cmd)
    def verify(self,pid):
        pid_l=self._server.get_pid('ping')
        while pid in pid_l:
            time.sleep(1)
            pid_l=self._server.get_pid('ping')
        cmd='cat nohup.out'
        self._server.ex_cmd(cmd)
        time.sleep(1)
        icmp_l=self._server.read_all().split('\r\n')
        index1=icmp_l.index(self._icmp_str1)+1
        if self._icmp_str2 in icmp_l:
            index2=icmp_l.index(self._icmp_str2)-1
        else:
            index2=len(icmp_l)-1
        icmp_l2=icmp_l[index1:index2]
        icmp_s='\n'.join(icmp_l2)
        length=len(icmp_l2)
        s1='\d+ bytes from {dest}: icmp_seq=\d+ ttl=\d+ time[=<][\d+.]+ ms'.format(dest=self._dest)
        sre=re.compile(s1)
        lines=re.findall(sre,icmp_s)
        return length,len(lines)
    def close(self):
        self._server.close()
class SSH():
    def __init__(self,server,username,password,dest,cmd=''):
        self._uid=username
        self._psword=password
        self._dest=dest
        self._server=server
        #get_ssh(self._src,22,'root','asd123456')
        self._cmd=cmd
    def start(self):
        ssh_cmd='sshpass -p {psword} ssh {uid}@{dest} &'.format(psword=self._psword,\
                uid=self._uid,dest=self._dest)
        time.sleep(1)
        self._server.read_all()
        self._server.ex_cmd(ssh_cmd)
        time.sleep(1)
        s=''.join(self._server.read_all().split('\r\n'))
        #print s
        if 'Welcome' in s:
            state=True
        else:
            state=False
        return state
    def stop(self):
        stop_cmd='killall sshpass'
        self._server.ex_cmd(stop_cmd)
    def close(self):
        self._server.close()
#################################################################
server=get_ssh('10.11.123.160',22,'root','asd123456')
if server.state:
    '''icmp=ICMP(server,'10.11.123.161','eth0',200)
    pid=icmp.start()
    time.sleep(20)
    icmp.stop(pid)
    print icmp.verify(pid)'''
    ssh=SSH(server,'root','asd123456','10.11.123.169')
    print ssh.start()
    time.sleep(20)
    ssh.stop()
else:
    print 'eee'
