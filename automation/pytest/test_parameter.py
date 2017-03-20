#coding:utf-8
import pytest
#pytest.mark.parametrize
#构造迭代参数case
@pytest.mark.parametrize("input1,expected", [
("3+5", 8),
("2+4", 6),
("6*9", 42),
])
def test_eval(input1, expected):
    assert eval(input1) == expected
#tmpdir 打印当前目录（内置变量）
def test_tt(tmpdir):
    print tmpdir
    assert False
