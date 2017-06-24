# -*- coding: utf-8 -*-
import requests
import os
from openpyxl import Workbook
from openpyxl import load_workbook
from bs4 import BeautifulSoup
import time

def get_all_xian_qu_urls():
    base_url='http://chongqing.11467.com/'
    header= {
                'Connection':'close',
                'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
                }
    res=requests.get(base_url,headers=header,timeout=(3.05, 27))
    soup = BeautifulSoup(res.content,'html.parser')
    with open('test.html','w') as f:
        f.write(res.text)
    all_dt_tag=soup.find_all('dt')
    #print(all_dt_tag)
    for dt in all_dt_tag:
        if '梁平县' in dt.get_text():
            print('梁平县')
            i=all_dt_tag.index(dt)
        if '璧山县' in dt.get_text():
            print('璧山县')
            j=all_dt_tag.index(dt)
    xian_qu_urls=[]
    for index in range(i,j):
        xian_qu_urls.append(all_dt_tag[index].find('a').get('href'))
    return xian_qu_urls
def get_xian_qu_all_page_urls(quxians_url):
    header= {
                'Connection':'close',
                'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
                }
    #获取页数
    page_urls=[]
    for quxian_url in quxians_url:
        try:
            res=requests.get(quxian_url,headers=header,timeout=(3.05, 27))
            soup = BeautifulSoup(res.content,'html.parser')
            pages=soup.find_all('div',{'class':'pages'})
            #print(pages)
            if pages:
                max_page_num=pages[0].find_all('a')[-1].get('href').replace(quxian_url+'pn','')
                for num in (1,int(max_page_num)):
                    page_urls.append(quxian_url+'pn'+str(num))
            else:
                print(quxian_url+':分页url获取失败')
            time.sleep(5)
        except Exception as e:
            print(e)
            print(quxian_url+':分页url获取失败')
        
    return page_urls
def get_xianqu_page_company_name(pages_url,filename):
    header= {
                'Connection':'close',
                'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
                }
    path=os.path.join(os.path.abspath('.'),filename+'.xlsx')
    if os.path.exists(path):
        wb = load_workbook(self.path)
        ws1=wb.get_sheet_by_name('公司名字')
    else:
        wb = Workbook()
        ws1=wb.create_sheet('公司名字',0)
    for page_url in pages_url:
        try:
            print('第{index}页公司爬取中.....'.format(index=pages_url.index(page_url)))
            res=requests.get(page_url,headers=header,timeout=(3.05, 27))
            soup = BeautifulSoup(res.content,'html.parser')
            company_list=soup.find_all('ul',{'class':'companylist'})
            all_li_tag=company_list[0].find_all('li')
            for li in all_li_tag:
                company_name=li.find('h4').get_text()
                row_max=ws1.max_row
                ws1.cell(row =row_max+1, column =1, value=company_name)
            time.sleep(5)
        except Exception as e:
            print(e)
            print(page_url+':页面爬取失败.')
if __name__=='__main__':
    quxians_url=get_all_xian_qu_urls()
    pages_url=get_xian_qu_all_page_urls(quxians_url)
    get_xianqu_page_company_name(pages_url,'重庆公司')
