from my_module.login_vclient import *
from my_module import cf
from my_module import check_time
from my_module import login_vclient
import threading
import HTMLTestRunner
import unittest
def change_interface():
    print time.time()
    time.sleep(10)
    set_interface4(True)
    time.sleep(4)
    set_interface4()
class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.cf_r=cf.config()
    def test_hold_down_time(self):
        if self.cf_r:
            login_vclient.login_client(path)
            pw1=threading.Thread(target=change_interface)
            pw2=threading.Thread(target=check_time.check_hold_down_time,args=(self.cf_r[0],))
            threads=[pw1,pw2]
            for t in threads:
                t.setDaemon(True)
                t.start()
            t.join()
            #self.assertEqual(tt,self.cf_r[1], 'test case2 sum fail')
            tt=check_time.buff.getvalue()
            self.assertLessEqual(abs(float(tt)-self.cf_r[1]),1,'msg')
        else:
            pass
if __name__=='__main__':
    testunit=unittest.TestSuite()
    #�������������뵽����������
    testunit.addTest(MyTestCase('test_hold_down_time'))

    #�����������·����֧�����·��
    filename = 'result.html'

    fp = open(filename, 'wb')
    #������Ա���
    runner =HTMLTestRunner.HTMLTestRunner(
    stream=fp,
    title=u'�ٶ��������Ա���',
    description=u'����ִ�������')
    #���в�������
    runner.run(testunit)
    fp.close()
