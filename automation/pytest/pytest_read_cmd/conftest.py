#coding:utf-8
import pytest
#注册一个参数
def pytest_addoption(parser):
    parser.addoption("--runslow", action="store",
        help="run slow test")
from test_read import Foo
#自定义错误输出
def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Foo) and isinstance(right, Foo) and op == "==":
        return ['Comparing Foo instances:',
               '   vals: %s != %s' % (left.val, right.val)]
