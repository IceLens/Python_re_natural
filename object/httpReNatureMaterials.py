import codecs
import hashlib
import json
import re
import time
import multiprocessing
import jieba
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from include.tt_draw import *

# import random
# import os
'''
    本程序为了方便,将所有函数整合于单一文件
    
    But 程序不应该有这么多缩进......
'''


# Requests 获取HTML页面
def get_html(url, timeout=60, rand=0):
    if rand == 0:
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50'}
    else:
        ua = UserAgent(browsers=['edge', 'chrome'])
        headers = ua.random

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        print(e)
        pass


# 获取文章摘要
def get_abstract(url, href):
    html = get_html(url + href)
    soup = BeautifulSoup(html, "lxml")

    text = soup.find(attrs={"id": "Abs1-content"}).select('p')[0]
    text = str(text)
    if text is not None:
        return text
    else:
        return 'None'


# 字符换行
def wrap_two(text):
    str(text)
    text = text.replace('。', '\n')
    text = text.replace('.', '.\n')
    return text


# 文档字符剔除
def del_character_doc(infile='', outfile='', change_to=' '):
    in_fo_open = open(infile, 'r', encoding='utf-8')
    out_fo_open = open(outfile, 'w', encoding='utf-8')
    db = in_fo_open.read()
    # 需清除的字符
    char_list = [' ']
    for char in char_list:
        out_fo_open.write(db.replace(char, change_to))

    in_fo_open.close()
    out_fo_open.close()
    # os.remove(infile)


def web_change(tag):
    tag = tag.find(attrs={"class": "c-card__link u-link-inherit"}).get_text()
    tag_hash = hashlib.md5(tag.encode()).hexdigest()

    if not os.access('save files/hash.json', os.R_OK):
        with open('save files/hash.json', 'w') as f:
            hash_dic = {"hash": "None"}
            json.dump(hash_dic, f, indent=4, ensure_ascii=False)

    try:
        with open('save files/hash.json', 'r') as f:
            cache_hash = json.load(f)
            # 如相等则返回False
            if cache_hash['hash'] == tag_hash:
                return False
            else:
                cache_hash['hash'] = tag_hash
        # 如不等则返回True
        with open('save files/hash.json', 'w') as r:
            json.dump(cache_hash, r)
            return True

    except Exception as e:
        print(e)
        os.unlink('save files/hash.json')
        return True


# BeautifulSoup 处理HTML以提取信息
def text_analysis(soup, if_trans='0', url='https://www.nature.com'):
    i = 0
    # 获取每个文本盒子
    for tag in soup.find_all(attrs={"class": "app-article-list-row__item"}):
        try:
            # 文本处理
            # 标题
            title_link = tag.find(attrs={"class": "c-card__link u-link-inherit"})
            title = re.sub('(</?a.*?>)|(</?p>)', '', str(title_link))
            # 简介
            summary = tag.find(attrs={"class": "c-card__summary u-mb-16 u-hide-sm-max"}).select('p')[0]
            summary = re.sub('(</?a.*?>)|(</?p>)', '', str(summary))
            # 文章链接'a'标签
            link = title_link.get('href')
            # 文章发布时间
            pub_time = tag.select("time[class='c-meta__item c-meta__item--block-at-lg']")
            pub_time = pub_time[0].get_text()

            # 输出处理后文本
            if title and summary is not None:
                # 序号
                i += 1
                # 获取摘要
                abstract = get_abstract(url, link)
                abstract = re.sub('(</?a.*?>)|(</?p>)', '', abstract)

                # 翻译模式
                if if_trans == '1':
                    title = baidu_translate(title)
                    summary = baidu_translate(summary)
                    abstract = baidu_translate(abstract)
                    print('翻译完成')

                # 调取wrap以换行文本
                summary, abstract = wrap_two(summary), wrap_two(abstract)
                del_char_list = ('＜sub＞', '＜/su＞')
                change_char_list = ('<sub>', '</sub>')

                for char_index in range(1):
                    summary = summary.replace(del_char_list[char_index], change_char_list[char_index])
                    abstract = abstract.replace(del_char_list[char_index], change_char_list[char_index])

                print(
                    f"{i}. \n标题:{title}. \n简介:{summary} \n摘要:{abstract} \n文章链接:{url}{link} \n发布时间:{pub_time}\n")
                # 将文本写入文件
                inFoFile.write(f'{str(i)}\n'
                               f' ## {title}.\n'
                               f' <b>{summary}</b>\n\n'
                               f' [摘要]  \n{abstract}\n\n'
                               f' [文章链接]\n{url + link}\n\n'
                               f' [发布时间]  \n{pub_time}\n\n'
                               f' ***\n\n'
                               )
                if i % 3 == 0:
                    inFoFile.flush()
            else:
                continue

        except Exception as e:
            print(e)
            pass


# BaiduAPI 翻译
def baidu_translate(text, flag=0):
    # 检测本地是否有配置文件
    if os.path.isfile(path + file_name):
        api_list = json_api_read(path + file_name)
        api_id = api_list['api_id']
        secret_key = api_list['secret_key']
    else:
        print('因安全问题,百度API需自行提供,输入后将保存')
        api_id = str(input('API账户'))
        secret_key = str(input('API密钥'))
        json_api_write(path, api_id, secret_key)

    baidu_api_url = 'https://api.fanyi.baidu.com/api/trans/vip/translate'
    from_lang = 'auto'

    # 翻译模式
    if flag == 1:
        to_lang = 'en'
    else:
        to_lang = 'zh'

    # 百度翻译api 要求格式
    try:
        salt = random.randint(3276, 65536)
        sign = api_id + text + str(salt) + secret_key
        sign = hashlib.md5(sign.encode()).hexdigest()
        data = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appid': api_id,
            'salt': str(salt),
            'sign': sign
        }

        res = requests.post(baidu_api_url, data=data)
        result = res.json()
        result = result['trans_result'][0]['dst']

        time.sleep(1)
        return result
    except Exception as e:
        print(e)


# TODO 尝试爬取翻译界面 百度翻译加密导致无法爬取
def baidu_trans_two(text):
    if type(text) is not str:
        raise TypeError
    exit('未完成')


# 获取ip属地以推测用户地址（没什么用）
def get_ip_address():
    url = 'https://2023.ip138.com//'
    try:
        html = get_html(url)
        soup = BeautifulSoup(html, 'lxml')

        ip_address = soup.find('p').get_text()
        ip_address = ip_address.replace('来自：', '')
        ip_address = ip_address.split()

        if ip_address is not None:
            ip_address = jieba.lcut(ip_address[2])
            # 为解决 jieba 分解字符问题(这貌似不是一个合理的办法,但似乎可以正常使用)
            if len(ip_address) > 4:
                ip_address = ip_address[1] + ip_address[2]
                return ip_address
            else:
                return ip_address[1]
        else:
            return None

    except Exception as e:
        print(e)


# 写入配置文件
def json_api_write(fdir, api_id, secret_key):
    if not os.path.exists(fdir):
        os.mkdir(fdir)
    # 使用json库
    with open(fr'{fdir}\api.json', 'w') as f:
        api_dict = {"api_id": api_id, "secret_key": secret_key}
        json.dump(api_dict, f, indent=4, ensure_ascii=False)


# 读取配置文件
def json_api_read(file_path):
    # 文件是否可读
    if not os.access(file_path, os.R_OK):
        return None
    # 读取json
    with open(f'{file_path}', 'r') as f:
        ini = json.load(f)
    return ini


def tt_draw(tt_type=0):
    if tt_type == 0:
        tt_draw_random()
    elif tt_type == 1:
        tt_draw_polyhedral()
    elif tt_type == 2:
        tt_draw_picture('https://www.yxlumen.com.cn/saveFiles/chicken_so_beautiful.png', 5, 0.5, 0.5)
    else:
        print('你干嘛,哎哟')


# Main function
def main():
    url_mat = 'https://www.nature.com/nmat/'

    request_headers_type = input('是否使用随机请求头\n y/n :  ')
    if request_headers_type == 'n':
        request_headers_type = 0
    else:
        print('已选择随机请求头')
        request_headers_type = 1

    print('开始爬取\n' + '——' * 30)
    html_nature = get_html(url_mat, request_headers_type)

    print('请求完成,正在解析文档')
    soup_main = BeautifulSoup(html_nature, "lxml")
    if web_change(soup_main):
        text_analysis(soup_main, trans)


# 程序开始
if __name__ == '__main__':
    # 欢迎语句
    address = get_ip_address()
    if address is not None:
        print(f'你好，来自{address}的用户')

    # 配置文件地址
    folder_dir = os.environ['APPDATA']
    file_name = 'api.json'
    path = folder_dir + '\\pyhttpRe\\'

    while True:
        # 选择
        trans = input('\n(0)原文;(1)翻译;(2)强制刷新;(3)重新输入密钥;(4)查询当前密钥;(5)清除密钥;(q)退出\r\n')

        if trans in ['0', '1']:
            break
        elif trans == '2':
            os.unlink('save files/hash.json')
        elif trans == '3':
            apiId = str(input('API账户: '))
            secretKey = str(input('API密钥: '))
            json_api_write(path, apiId, secretKey)
        elif trans == '4':
            api = json_api_read(path + 'api.json')
            if api is not None:
                print(f'API账户: {api["api_id"]}\nAPI密钥: {api["secret_key"]}')
            else:
                print('无密钥文件')
        elif trans == '5':
            a = input('确认清除?  y/n\n')
            if a == 'y':
                try:
                    os.remove(path + 'api.json')
                except FileNotFoundError:
                    print('无配置文件')
        elif trans[0:2] == 'tt':
            if len(trans) > 2:
                ttType = trans[-1]
                tt_drawing_process = multiprocessing.Process(target=tt_draw, args=(int(ttType),))
                tt_drawing_process.start()
            else:
                tt_drawing_process = multiprocessing.Process(target=tt_draw)
                tt_drawing_process.start()
        # 退出
        elif trans == 'q':
            exit('Exit')
        else:
            print('无此选项')

    if not os.path.exists('save files'):
        os.mkdir('save files')
    # 打开文档流
    inFoFile = codecs.open("./save files/temp-Nature.txt", 'w+', 'utf-8')
    inFoFile.write("")
    # 主函数
    main()
    # 关闭文档流
    inFoFile.close()
    date = time.strftime('%y-%m-%d')
    # 清除字符
    if os.path.getsize('./save files/temp-Nature.txt'):
        del_character_doc('./save files/temp-Nature.txt', f'./save files/{date}-Nature Materials.md')

    print(f'爬取完成,结果保存于{date}-Nature Materials.md')
    os.remove('./save files/temp-Nature.txt')

    time.sleep(5)
