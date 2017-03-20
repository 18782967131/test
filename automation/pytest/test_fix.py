import pytest
@pytest.fixture(scope="module",params=['10.11.123.140', "10.11.123.250"])
def smtp(request):
    import paramiko
    smtp = paramiko.SSHClient()
    smtp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    smtp.connect(request.param,22,'varmour','vArmour123')
    s=smtp.invoke_shell()
    def fin():
        print ("teardown smtp")
        smtp.close()
    request.addfinalizer(fin)
    return s  # provide the fixture value
def test_ssh(smtp):
    print smtp.recv(1024)
    print 'connect ok!'
    assert 0
