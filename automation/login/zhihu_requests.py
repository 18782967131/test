import requests
import re
from bs4 import BeautifulSoup
header = {  
    'Connection': 'Keep-Alive',  
    'Accept': 'text/html, application/xhtml+xml, */*',  
    'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',  
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',  
    'Accept-Encoding': 'gzip, deflate',  
    'Host': 'www.zhihu.com',  
    'DNT': '1'  
}
# Cookie:q_c1=ba0d15cdc172426b8b9560c9f3d2e5f4|1487319379000|1487319379000; nweb_qa=heifetz; cap_id="NmNhZjI3OTNkNDYyNDkxMmJiOWNiNTFhMWQzM2E4OWE=|1487319379|ea3579d3539a722ade064723893ebcda6a0108a6"; l_cap_id="NDllNDU0ZjcwOWMyNDEyMTlkNGI0YmY5M2RjZDVlZGI=|1487319379|153c3d69e1ca18a545e87e221ce7cb1b79ffc5ea"; d_c0="AGACQ9jcUguPTnYIFK86DoEk6-GZqbthUyU=|1487319381"; _zap=62b4897d-e2b3-4025-a573-67a410daf37f; __utma=51854390.1290969891.1487319399.1487319399.1487319399.1; __utmb=51854390.0.10.1487319399; __utmz=51854390.1487319399.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmv=51854390.000--|2=registration_date=20170217=1^3=entry_date=20170217=1; login="ZGE0M2QzOWRmYTRlNDZhNDkyZTc5N2VkZDVjY2UwNjU=|14 
url = 'http://www.zhihu.com/' 
s = requests.Session()
#allow_redirects=True允许重定向，timeout设置超时时间，verify绕过ssl验证,params post参数，cookies添加cookies
#代理
#proxies = {
# "http": "http://10.10.1.10:3128",
# "https": "http://10.10.1.10:1080",
#}
#requests.get("http://example.org", proxies=proxies)
#
data=s.get(url,headers=header)
re1=re.compile('_xsrf" value="(.+)"')
print(data.text,data.encoding,data.status_code,data.cookies,data.headers)
#读取html编码，赋值改变编码模式,响应状态,获取cookies,获取头部
print('+++++++++++++++')
p={
'_xsrf':re1.findall(data.text)[0],
'phone_num':'18782967131',
'password':'cj5596855'
}
url2='https://www.zhihu.com/login/phone_num'
#post,get,put
data1 = s.post(url2,params=p,verify=False,headers=header)
data2 = s.get('https://www.zhihu.com/#signin',headers=header)
print(data2.text)
with open('1.html','w+') as f:
	f.write(data2.text)
