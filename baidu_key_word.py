#coading:utf-8
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def append_kw(kw_list,result_list):
    for result in result_list:
        if result not in kw_list:
            kw_list.append(result)
    return kw_list
def get_relatewords(kw_list):
    header={
        'Connection':'keep-alive',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Host':'www.baidu.com'
        }
    for kw in kw_list:
        if len(kw_list)<1000:
            url='https://www.baidu.com/s?wd={kw}%&tn=baidurs2top'.format(kw=kw)
            print(url)
            r = requests.get(url,headers=header)
            c = r.content.decode('utf-8','ignore').split(',')
            print(c)
            kw_list=append_kw(kw_list,c)
        else:
            return kw_list
            break
    return kw_list
print(get_relatewords(['重庆渝开发']))
