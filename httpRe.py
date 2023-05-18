import codecs
import hashlib
import http.client
import json
import random
import urllib.parse
from time import sleep

import requests
from bs4 import BeautifulSoup

# 密钥
from baiduapi import api_id, secret_key


# Requests 获取HTML页面
def get_html(url, timeout=60):
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42'}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        print(e)
        pass


# BeautifulSoup 处理HTML以提取信息
def featured(soup, if_trans='n', url='https://www.nature.com'):
    i = 0
    inFoFile.write("")
    # 获取每个文本盒子
    for tag in soup.find_all(attrs={"class": "app-article-list-row__item"}):
        i += 1
        try:
            # 文本处理
            title_link = tag.find(attrs={"class": "c-card__link u-link-inherit"})
            title = title_link.string

            summary = tag.find(attrs={"class": "c-card__summary u-mt-0 u-mb-16 u-hide-sm-max"})
            summary = summary.select('p')[0].get_text()

            link = title_link.get('href')
            time = tag.select("time[class='c-meta__item c-meta__item--block-at-lg']")
            time = time[0].get_text()

            # 输出处理后文本
            if title and summary and time and link is not None:
                abstract = get_abstract(url, link)

                # 翻译模式
                if if_trans == 'y':
                    title = baidu_translate(title)
                    summary = baidu_translate(summary)
                    abstract = baidu_translate(abstract)
                elif if_trans == 'y2':
                    title = baidu_trans_two(title)
                    summary = baidu_trans_two(summary)
                    abstract = baidu_trans_two(abstract)

                summary, abstract = wrap_two(summary), wrap_two(abstract)
                print(
                    f"{i}. \n标题:{title}. \n简介:{summary} \n摘要:{abstract} \n文章链接:{url}{link} \n发布时间:{time}\n")
                inFoFile.write(
                    str(i) + '.\r\n' +
                    '[标题]\n' + title + '.\r\n' +
                    '[简介]  \n' + summary + '\r\n' +
                    '[摘要]  \n' + abstract + '\r\n' +
                    '[文章链接]\n' + url + link + '\r\n' +
                    '[发布时间]\n' + time + '.\r\n\n')
            else:
                continue

        except Exception as e:
            print(e)
            pass


# 获取文章摘要
def get_abstract(url, href):
    html = get_html(url + href)
    soup = BeautifulSoup(html, "lxml")

    text = soup.find(attrs={"id": "Abs1-content"}).string
    if text is not None:
        return text
    else:
        return 'None'


# 字符换行
def wrap(text):
    str(text)
    text = text.split()
    index = len(text)

    # 每16个字符换行
    for i in range(0, index, 16):
        text.insert(i, '\n')

    # 连接列表元素并分隔
    text[0] = ' '
    return " ".join(text)


def wrap_two(text):
    str(text)
    text = text.replace('。', '\n')
    text = text.replace('.', '.\n')
    return text


# BaiduAPI 翻译
def baidu_translate(text, flag=0):
    http_client = None
    my_url = '/api/trans/vip/translate'
    from_lang = 'auto'

    # 翻译模式
    if flag == 1:
        to_lang = 'en'
    else:
        to_lang = 'zh'

    salt = random.randint(3276, 65536)

    try:
        # 编码字符
        sign = api_id + text + str(salt) + secret_key
        sign = hashlib.md5(sign.encode()).hexdigest()
        my_url = my_url + '?appid=' + api_id + '&q=' + urllib.parse.quote(text) + '&from=' + from_lang + \
                 '&to=' + to_lang + '&salt=' + str(salt) + '&sign=' + sign

        # 请求
        http_client = http.client.HTTPConnection('api.fanyi.baidu.com')
        http_client.request('GET', my_url)
        response = http_client.getresponse()
        # 编码获取的结果
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        result = result['trans_result'][0]['dst']

        sleep(1)
        return result

    except Exception as e:
        print(e)
    finally:
        if http_client:
            http_client.close()


# 尝试爬取翻译界面
def baidu_trans_two(text):
    if type(text) is not str:
        raise TypeError
    html = 'https://fanyi.baidu.com/v2transapi?from=en&to=zh'
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42'}
    params = {
        'from: en',
        'to: zh',
        'query: auto',
        'simple_means_flag: 3',
        'sign: 465243.260714',
        'token: 632ef57cc83b88b230fab9eaedcee5d0',
        'domain: common',
        'ts: 1684404720952'
    }
    res = requests.post(html, headers=headers, params=params)


trans = str(input('(n)原文;(y)翻译\r\n'))
# 打开文档流
inFoFile = codecs.open("Nature Materials.txt", 'w+', 'utf-8')
url_mat = 'https://www.nature.com/nmat/'

htmlNature = get_html(url_mat)
soupMain = BeautifulSoup(htmlNature, "lxml")
featured(soupMain, trans)

inFoFile.close()
