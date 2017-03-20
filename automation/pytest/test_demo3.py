import pytest
@pytest.mark.xfail(raises=IndexError)
def test_function():
        f()
def test_function2():
        assert False
