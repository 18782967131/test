import requests
from requests.auth import HTTPBasicAuth
class get_64base_error(Exception):
    def __init__(self,value):
        self.value=value
        super().__init__()
    def __str__(self):
        return repr(self.value)
class cheack_login_error(Exception):
    def __init__(self,value):
        self.value=value
        super().__init__()
    def __str__(self):
        print('str')
        return repr(self.value)
class rest_api():
    def __init__(self):
        self.session=requests.Session()
    def get_64base(self,ip,username,password):
        self.ip=ip
        self.username=username
        self.password=password
        self.auth=''
        _url='https://{ip}/api/v1.0/auth'.format(ip=self.ip)
        headers = {'content-type': 'application/json',
           'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}
        self.session.headers.update(headers)
        #基本验证
        auth=HTTPBasicAuth(self.username,self.password)
        #获取64位加密passwd
        re=self.session.post(_url,auth=auth,verify=False)
        check_url='https://{ip}/api/v1.0/operation/system/login_info'.format(ip=self.ip)
        if re.status_code==200:
            #带着64位加密passwd访问
            url='https://{ip}/api/v1.0/config/hierarchy'.format(ip=self.ip)
            self.auth=HTTPBasicAuth(self.username,re.json()['auth'])
        else:
            raise get_64base_error('get 64 base passwd fail')
        if self.cheack_64base():
            pass
        else:
            raise cheack_login_error(self.s)
    def cheack_64base(self):
        check_url='https://{ip}/api/v1.0/config/hierarchy'.format(ip=self.ip)
        re=self.session.get(check_url,auth=self.auth,verify=False)
        self.s=''
        if re.status_code==200:
            print(re.text)
            return True
        else:
            self.s=re.text
            return False
    def get(self,url):
        self.url=url
        re=self.session.get(self.url,verify=False)
        return re.json(),re.status_code
rest=rest_api()
rest.get_64base('10.11.123.250','varmour','vArmour123')