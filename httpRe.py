import hashlib
import http.client
import json
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup
import codecs


# Requests 获取HTML页面
def get_html(url, timeout=60):
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) '
                             'Chrome/99.0.4844.35 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        print(e)
        pass
        # exit('Something  wrong')


# BeautifulSoup 处理HTML以提取信息
def featured(soup, url='https://www.nature.com', trans=0):
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
                summary, abstract = wrap(summary), wrap(abstract)

                if trans == 0:

                print(
                    f"{i}. \n标题:{title}. \n简介:{summary} \n摘要:{abstract} \n文章链接:{url}{link} \n发布时间:{time}\n")

                inFoFile.write(
                    str(i) + '.\r\n' +
                    '[标题]\n' + title + '.\r\n' +
                    '[简介]\n' + summary + '\r\n' +
                    '[摘要]\n' + abstract + '\r\n' +
                    '[文章链接]\n' + url + link + '\r\n' +
                    '[发布时间]\n' + time + '.\r\n\n')
            else:
                continue

        except AttributeError as e:
            print(e)
            pass
        except Exception as e:
            print(e)
            pass


def get_abstract(url, href):
    html = get_html(url + href)
    soup = BeautifulSoup(html, "html.parser")

    text = soup.find(attrs={"id": "Abs1-content"}).string
    if text is not None:
        return text
    else:
        return 'None'


# BaiduAPI
def translation(text, flag=1):
    api_id = ''
    secret_key = ''
    http_client = None
    my_url = '/api/trans/vip/translate'
    from_lang = 'auto'

    if flag == 1:
        to_lang = 'zh'
    else:
        to_lang = 'en'

    salt = random.randint(3276, 65536)

    sign = api_id + text + str(salt) + secret_key
    sign = hashlib.md5(sign.encode()).hexdigest()
    my_url = my_url + '?appid=' + api_id + '&q=' + urllib.parse.quote(text) + '&from' + from_lang + \
             '&to=' + to_lang + '&salt=' + str(salt) + '&sign=' + sign

    try:
        http_client = http.client.HTTPConnection('api.fanyi.baidu.com')
        http_client.request('GET', my_url)
        response = http_client.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)

        return result['trans_result'][0]['dst']
    except Exception as e:
        print(e)
    finally:
        if http_client:
            http_client.close()


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


def main():
    url_mat = 'https://www.nature.com/nmat/'

    html = get_html(url_mat)
    soup = BeautifulSoup(html, "html.parser")
    featured(soup)


# 打开文档流
inFoFile = codecs.open("Nature Materials.txt", 'w+', 'utf-8')
main()

inFoFile.close()
