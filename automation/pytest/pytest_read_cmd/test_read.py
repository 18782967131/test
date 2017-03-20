#coding:utf-8
import pytest
'''def test_fast():
    print 'fast'
    assert 0
#没有--runshow cmd参数跳过test_slow case
@pytest.mark.skipif(not pytest.config.getoption('--runslow')
,reason='need --runslow option to run')
def test_slow():
    print 'slow'
    assert 0'''
#重写比较的魔法方法
class Foo:
    def __init__(self, val):
         self.val = val
    def __eq__(self, obj):
        return self.val == obj.val
def test_compare():
    f1 = Foo(1)
    f2 = Foo(1)
    assert f1 == f2
