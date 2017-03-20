import pytest
@pytest.fixture
def tt():
   return 'ttttddd'
def test_sk(tt):
    assert tt.upper()=='TTTTDDD'
