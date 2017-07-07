# -*- coding: utf-8 -*-
import requests
import os
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl import load_workbook

page=1
base='http://office.cq.fang.com/loupan/house/i3{page}/'.format(page=page)
def get_base_page(url):
    header={
            'Connection':'close',
            'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
            }
    res=requests.get(base,headers=header)
    soup=BeautifulSoup(res.text,'html.parser')
    dl_tags=soup.find_all('dl',{'class':'list rel'})
    price_p_tags=soup.find_all('p',{'class':'mt5'})
    for dl in dl_tags:
        if len(dl_tags)*2==len(price_p_tags):
            #print(price_p_tags[dl_tags.index(dl)].text,price_p_tags[dl_tags.index(dl)+1].text)
            s1=price_p_tags[dl_tags.index(dl)].text
            s2=price_p_tags[dl_tags.index(dl)+1].text
            if '售价' in s1:
                print('售价:'+s1[3:])
                print('租金:'+s2[3:])
            else:
                print('售价:'+s2[3:])
                print('租金:'+s1[3:])
        p_tags=dl.find('dd').find_all('p')
        for p in p_tags:
            #print(p.text)
            s=p.text.strip()
            if 'title' in p.get('class'):
                print('名字0:'+s)
                #print(s,s.startswith('类型'))
            if 'mt10' in p.get('class'):
                a_tags=p.find_all('a')
                for a in a_tags:
                    if '出租房源' in a.text:
                        url1=a.get('href')
                    elif '出售房源' in a.text:
                        url2=a.get('href')
            if s.startswith('类型'):
                if '物业费' in s:
                    print('类型1:'+s[3:s.find('物业费')].strip())
                    print('物业费2:'+s[s.find('物业费')+4:].strip())
                else:
                    print('类型3:'+s[3:].strip())
            elif s.startswith('地址'):
                print('地址4:'+s[3:s.find('地图交通')].strip())
            elif s.startswith('竣工日期'):
                print('竣工日期5:'+s[5:].strip())
def chushou(url):
    #url='http://zongbuchengcq.fang.com/office/chushou'
    header={
                    'Connection':'close',
                    'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
                    }
    res=requests.get(url,headers=header)
    soup=BeautifulSoup(res.text,'html.parser')
    page_tag=soup.find('li',{'class':'pages floatr'})
    max_page=1
    if page_tag:
        s=page_tag.text.strip()
        max_page=int(s[:s.find('页')].strip().split('/')[1])
    info_url=[]
    for i in range(1,max_page+1):
        true_url=url+'list/-i{page}/'.format(page=str(30+i))
        res=requests.get(url,headers=header)
        soup=BeautifulSoup(res.text,'html.parser')
        div=soup.find('div',{'class':'list_pic'})
        info_div=div.find_all('div')
        for div in info_div:
            if 'house' in div.get('class'):
                if len(div.find('p',{'class':'gray9 time'}).find_all('a'))>1:
                    info_url.append(div.find('p',{'class':'gray9 time'}).find_all('a')[1].get('href'))
    #print(info_url)
    for url in info_url:
        phase_chushou(url)
def phase_chushou(url):
    print(url)
    header={
                    'Connection':'close',
                    'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
                    }
    res=requests.get(url,headers=header)
    soup=BeautifulSoup(res.text,'html.parser')
    phone_div=soup.find('div',{'class':'phone_top'})
    if phone_div:
        print('电话号码:'+phone_div.find('label',{'id':'mobilecode'}).text)
    info_div=soup.find('div',{'class':'inforTxt'})
    if info_div:
        s=info_div.find('dt',{'class':'gray6 zongjia1'}).text.replace('\n','').strip()
        if '总价' in s:
            print('总价:'+s[3:])
        for dd in info_div.find_all('dd',{'class':'gray6'}):
            #print(dd.text.replace('\n','').strip())
            s=dd.text.replace('\n','').strip()
            if '建筑面积' in s:
                print('建筑面积:'+s[s.find('建筑面积')+5:])
        dl_tags=info_div.find_all('dl')
        if len(dl_tags)>1:
            dt_tags=dl_tags[1].find_all('dt')
            dd_tags=dl_tags[1].find_all('dd')
            for dt in dt_tags:
                s=dt.text.strip()
                if '楼盘名称' in s:
                    print('楼盘名称：'+s[5:s.find('(')])
                if '楼盘地址' in s:
                    print('楼盘地址：'+s[5:])
            for dd in dd_tags:
                s=dd.text.replace('\n','').replace(' ','').strip()
                if '所在楼层' in s:
                    print('所在楼层：'+s[5])
                if '等级' in s:
                    print('等级：'+s[3])
                if '装修' in s:
                    print('装修：'+s[3])
                if '类型' in s:
                    print('类型：'+s[3])
chushou('http://zongbuchengcq.fang.com/office/chushou')