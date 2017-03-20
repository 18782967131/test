import myssh
import random
import time
def config(ip='10.11.123.140',user='varmour',password='vArmour123'):
    ssh=myssh.zdy_ssh(ip,22,user,password)
    time.sleep(2)
    vm=random.randint(1,256)
    pair=random.randint(1,8)
    ht=random.randint(8,16)
    cf1='set vwire-group vw{} interface-pair {} xe-2/0/2 with xe-2/0/3'.format(vm,pair)
    cf2='set vwire-group vw{} hold-down-time {}'.format(vm,ht)
    print ssh.state
    if ssh.state:
        if ssh.check_end('varmour@vArmour#ROOT> '):
            end='varmour@vArmour#ROOT> '
            cf='varmour@vArmour#ROOT(config)> '
        else:
            end='varmour@vArmour#ROOT(M)> '
            cf='varmour@vArmour#ROOT(config)(M)> '
        ssh.ex_cmd('configure')
        ssh.expect_end(cf)
        ssh.ex_cmd(cf1)
        ssh.expect_end(cf)
        ssh.ex_cmd(cf2)
        ssh.expect_end(cf)
        ssh.ex_cmd('commit')
        ssh.close()
        return ['vw'+str(vm),ht]
    else:
        try:
            ssh.close()
        except:
            pass
        return 0
if __name__=='__main__':
    config()
