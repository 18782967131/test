#coading:utf-8
#https://baike.baidu.com/search/word?word=%E6%9D%8E%E7%99%BD&sefr=enterbtn
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import gzip
'''header = {
'Host':'baike.baidu.com',
'Connection':'keep-alive',
'Upgrade-Insecure-Requests':'1',
'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
'Referer': 'https://baike.baidu.com/',
'Accept-Encoding': 'gzip, deflate, sdch, br',
'Accept-Language':'zh-CN,zh;q=0.8'
}
int=input('输入名字:')
old_url=r'https://baike.baidu.com/search/word?word={keys_word}'.format(keys_word=int)
url=quote(old_url,safe='/:?=')
print(url)
data=requests.get(url,headers=header).content
soup = BeautifulSoup(data, 'html.parser')
print(soup.find('dd', class_="lemmaWgt-lemmaTitle-title").find("h1").text)
print('+++++++++++++++++')
print(soup.find('div', class_="lemma-summary").text)'''
class baidu_spider():
    def __init__(self,name):
        self.name=name
        self.header={
        'Host':'baike.baidu.com',
        'Connection':'keep-alive',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://baike.baidu.com/',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language':'zh-CN,zh;q=0.8'
        }
    def make_url(self):
        old_url=r'https://baike.baidu.com/search/word?word={keys_word}'.format(keys_word=self.name)
        return quote(old_url,safe='/:?=')
    def get_page(self,url):
        response=requests.get(url,headers=self.header)
        if response.status_code==200:
            return response.content
        else:
            return False
    def html_parser(self,soup):
        title=soup.find('dd', class_="lemmaWgt-lemmaTitle-title").find("h1").text
        summary=soup.find('div', class_="lemma-summary").text
        return title,summary
    def set_name(self,name):
        self.name=name
    def run(self):
        #访问失败返回False
        url=self.make_url()
        data=self.get_page(url)
        soup = BeautifulSoup(data,'html.parser')
        if soup:
            return self.html_parser(soup)
        else:
            return False
libai=baidu_spider('李白')
print(libai.run())
libai.set_name('毛泽东')
print(libai.run())