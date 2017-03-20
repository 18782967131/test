import myssh
import time
import sys
from StringIO import StringIO
buff =StringIO()
def check_hold_down_time(vw,ip='10.11.123.140',user='varmour',password='vArmour123'):
    print time.time()
    global buff
    temp = sys.stdout
    sys.stdout = buff 
    t=0
    li=[]
    ssh=myssh.zdy_ssh(ip,22,user,password)
    time.sleep(2)
    if ssh.state:
        if ssh.check_end('varmour@vArmour#ROOT> '):
            end='varmour@vArmour#ROOT> '
        else:
            end='varmour@vArmour#ROOT(M)> '
        cmd='show vwire-group {}'.format(vw)
        while t<2:
            ssh.ex_cmd(cmd)
            s1=ssh.expect_end(end)
            ssh.ex_cmd(cmd)
            s2=ssh.expect_end(end)
            if s1!=s2:
                t=t+1
                li.append(time.time())
    else:
        ssh.close()
        print 0
    ssh.close()
    print li[1]-li[0]
    sys.stdout =temp 
