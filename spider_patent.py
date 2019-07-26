# -*- encoding: UTF-8 -*-

import requests
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import time
from pyquery import PyQuery as pq
from tqdm import tqdm

url = 'http://pss-system.cnipa.gov.cn/sipopublicsearch/portal/uiIndex.shtml'
# http://pss-system.cnipa.gov.cn/sipopublicsearch/patentsearch/searchHomeIndex-searchHomeIndex.shtml

df = pd.read_csv('test.csv', index_col=0)
li = df.set_index('公司全称').to_dict()['已发行股票']
# li = [ '宝山钢铁股份有限公司']

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--user-data-dir=/Users/jeep/pachong/Google')
browser = webdriver.Chrome(options=chrome_options)

browser.get(url)
input('login')
for each in tqdm(li):
    # each = each.replace('(', '（').repalce(')', '）')
    while True:
        browser.get(url)
        # input('login')
        myinput = browser.find_element_by_id('search_input')
        myinput.send_keys(each)
        browser.find_element_by_id('right_icon').click()
        # browser.find_element_by_id('radioTypeCongregatePAVIEW').click()
        myinput.send_keys(Keys.ENTER)

        wait = WebDriverWait(browser, 30)
        wait.until(EC.presence_of_element_located((By.ID, 'result_view_mode')))

        # browser.execute_script("$('#result_view_mode > a.btn.result-style-btn.list-style-btn').click()")



        s = browser.find_element_by_css_selector("#page_top > div > div > div").text
        page = int(re.findall(r'共 (.*?) 页',s)[0])
        num = int(re.findall(r'共 .*? 页 (.*?) ?条',s)[0])
        df = pd.DataFrame(columns=['公司','代码','标题','申请日','申请号','公开号','公开日','ipc1','ipc2'])

        with open('log/log.txt') as f:
            try:
                bp = int(f.read())
                df = df.append(pd.read_csv('log/temp.csv',index_col=0),ignore_index=True)
                nw = False
            except ValueError:
                bp = 0
                nw = True

        for i in range(bp,page):
            # df = df.append(pd.read_html(browser.page_source),ignore_index=True)
            html = browser.page_source
            doc = pq(html)
            title = doc('#resultMode > div > div.list-container > ul > li > div > div.item-header.clear > h1 > div:nth-child(2) > a > b')
            title = list(map(lambda x : x.text_content(),title))

            sqh = doc('#resultMode > div > div.list-container > ul > li > div > div.item-content.clear > div.item-content-body.left > p:nth-child(1)')
            sqh = list(map(lambda x : x.text_content()[6:],sqh))

            sqr = doc('#resultMode > div > div.list-container > ul > li > div > div.item-content.clear > div.item-content-body.left > p:nth-child(2) > a')
            sqr = list(map(lambda x : x.text_content(),sqr))

            gkh = doc('#resultMode > div > div.list-container > ul > li > div > div.item-content.clear > div.item-content-body.left > p:nth-child(3)')
            gkh = list(map(lambda x : x.text_content()[10:],gkh))

            gkr = doc('#resultMode > div > div.list-container > ul > li > div > div.item-content.clear > div.item-content-body.left > p:nth-child(4) > a')
            gkr = list(map(lambda x : x.text_content(),gkr))

            ipc1 = doc('#resultMode > div > div.list-container > ul > li > div > div.item-content.clear > div.item-content-body.left > p:nth-child(5)')
            ipc1 = list(map(lambda x : x.text_content().replace('\t','').replace(' ',''),ipc1))
            
            ipc2 = doc('#resultMode > div > div.list-container > ul > li > div > div.item-content.clear > div.item-content-body.left > p:nth-child(7)')
            ipc2 = list(map(lambda x : x.text_content().replace('\t','').replace(' ',''),ipc2))
            
            ipc=[]

            for j in range(len(ipc1)):
                if ipc1[j][0] == 'I':
                    ipc.append(ipc1[j])
                else:
                    ipc.append(ipc2[j])

            ipc1 = list(map(lambda x : x.split(':')[0],ipc))
            ipc2 = list(map(lambda x : x.split(':')[1],ipc))
            # sqr1 = doc('#resultMode > div > div.list-container > ul > li > div > div.item-content.clear > div.item-content-body.left > p:nth-child(6) > span > a > font')
            # sqr1 = list(map(lambda x : x.text_content(),sqr1))
            t = pd.DataFrame([title,sqh,sqr,gkh,gkr,ipc1,ipc2]).T
            t.columns = ['标题','申请日','申请号','公开日','公开号','ipc1','ipc2']
            if nw:
                df = df.append(t,ignore_index=True)
                df.to_csv('log/temp.csv')
                with open('log/log.txt','w') as f:
                    f.write(str(i))
            nw = True
            # browser.execute_script("$('#page_top > div > div > div > a:nth-child(3) > img').click()")
            myinput = browser.find_element_by_id('txt')
            myinput.clear()
            myinput.send_keys(i+2)
            myinput.send_keys(Keys.ENTER)

            while True:
                try:
                    while i != int(browser.find_element_by_css_selector("#resultMode > div > div.re-page > div > div > div > div > a.active").text)-2:
                        time.sleep(0.3)
                        if i == page - 1:
                            break
                    break
                except:
                    print('waiting')

        if num == len(df.index):
            df['公司']=each
            # df['代码']=li[each]
            with open('log/log.txt','w') as f:
                pass
            break
        else:
            print("应收"+str(num)+','+"实收"+str(len(df.index)))
            df.to_csv('log/erroe.csv')
            input('需手动判断是否重新下载：')
    # df.to_csv(each+'.csv')
    df.to_csv('allAtech.csv', mode='a', header=False)
browser.quit()
