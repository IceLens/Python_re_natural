import codecs
import hashlib
import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, RLock

try:
    import jieba
except Exception as e:
    print(e)
    os.system("pip install jieba")
try:
    import requests
except Exception as e:
    print(e)
    os.system("pip install requests")
try:
    from bs4 import BeautifulSoup
except Exception as e:
    print(e)
    os.system("pip install bs4")
try:
    from fake_useragent import UserAgent
except Exception as e:
    print(e)
    os.system("pip install fake-useragent")

from include.tt_draw import tt_draw_random, tt_draw_polyhedral, tt_draw_picture


# Requests 获取HTML页面
def get_html(url: str, rand=False, do_re_try=True, re_try_times=5, timeout=60) -> str:
    headers = {'referer': 'https://www.nature.com/'}
    if not rand:
        headers[
            'User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                            'Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50'
    else:
        # 设置为True以便使用者计算机上没有配置文件而无法运行
        ua = UserAgent(use_external_data=True)
        headers['User-agent'] = ua.edge

    i = 0
    while i < re_try_times:
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            r.encoding = 'utf-8'
            return r.text
        except Exception as e:
            if i >= 6 or not do_re_try:
                print('\r\nget_html:  ', end='')
                print(e)
                break
            # 错误重试
            print(f'\rRetry connecting... {i + 1}/{re_try_times}', end='')
        finally:
            time.sleep(0.5)
            i += 1


# 字符换行
# 一开始使用字符计数,字符到达120字时插入换行符 \n
# 但是对于中文处理效果不尽人意
def wrap_two(text) -> str:
    str(text)
    text = text.replace('。', '\n')
    text = text.replace('.', '.\n')
    return text


# 文档字符修改
# 由于原 HTML 页面有特殊字符导致文本输出时带有 字符，同时无法在分析函数返回的文本中修改，故使用此函数。
def change_character_doc(infile: str, outfile: str, change_to=' '):
    in_fo_open = open(infile, 'r', encoding='utf-8')
    out_fo_open = open(outfile, 'w', encoding='utf-8')
    db = in_fo_open.read()
    # 需清除的字符
    char_list = [' ']
    for char in char_list:
        out_fo_open.write(db.replace(char, change_to))

    in_fo_open.close()
    out_fo_open.close()


# 计算 返回的 HTML 页面第一个标题是否有变化,如无变化则不在深入分析文本以节约时间
def web_change(tag: BeautifulSoup):
    try:
        # 第一个标题
        tag = tag.find(attrs={"class": "c-card__link u-link-inherit"}).get_text()
        # 计算 md5 值
        tag_hash = hashlib.md5(tag.encode()).hexdigest()
    except Exception as e:
        print('web_change:  ', end='')
        print(e)
        return True
    # 保存 Hash 的文件是否存在
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
    # 出错则删除 hash.json 文件
    except Exception as e:
        print('web_change:  ', end='')
        print(e)
        os.unlink('save files/hash.json')
        return True


# BaiduAPI 翻译
# 一次请求过多会出现文本抛弃现象
def baidu_translate(text: str, flag=0, qps=1, max_require_length=1000) -> str:
    # 检测本地是否有配置文件
    if os.path.isfile(path + fileName):
        api_list = json_api_read(path + fileName)
        api_id = api_list['api_id']
        secret_key = api_list['secret_key']
    else:
        print('因安全问题,百度API需自行提供,输入后将保存')
        api_id = input('API账户')
        secret_key = input('API密钥')
        json_api_write(path, api_id, secret_key)

    baidu_api_url = 'https://api.fanyi.baidu.com/api/trans/vip/translate'
    from_lang = 'auto'

    # 翻译模式
    if flag == 1:
        to_lang = 'en'
    else:
        to_lang = 'zh'

    temp = []
    translated_strs = []
    if len(text) > max_require_length:
        temp = text.split('.')
    else:
        temp.append(text)
    for split_text in temp:
        try:
            # 百度翻译api 要求格式
            salt = random.randint(3276, 65536)
            sign = api_id + split_text + str(salt) + secret_key
            sign = hashlib.md5(sign.encode()).hexdigest()
            data = {
                'q': split_text,
                'from': from_lang,
                'to': to_lang,
                'appid': api_id,
                'salt': str(salt),
                'sign': sign
            }
            # 处理返回结果
            res = requests.post(baidu_api_url, data=data)
            result = res.json()
            result = result['trans_result'][0]['dst']
            translated_strs.append(result)
            # 普通接口每秒请求数限制
            qps = round(1 / qps, 2)
            time.sleep(qps)
        except Exception as e:
            print('baidu_translate:  ', end='')
            print(e)

    return ''.join(translated_strs)


# TODO 尝试爬取翻译界面 百度翻译加密导致无法爬取
# 预使用 Selenium 库的无头浏览器进行爬取,但应时间和兼容问题放弃
"""def baidu_trans_two(text):
    if type(text) is not str:
        raise TypeError
    exit('未完成')"""


def process_and_write(dic: dict):
    title = dic['title']
    summary = dic['summary']
    abstract = dic['abstract']
    link = dic['link']
    pub_time = dic['pub_time']

    # 翻译模式
    if select == 'y':
        # 调用翻译函数 加锁以避免请求过快
        translateLock.acquire()
        title = baidu_translate(title)
        summary = baidu_translate(summary)
        abstract = baidu_translate(abstract)
        translateLock.release()
        # 中文字符问题
        summary = summary.replace('＜', '<').replace('＞', '>')
        abstract = abstract.replace('＜', '<').replace('＞', '>')
        print('翻译完成')

    # 调取wrap以换行文本
    summary, abstract = wrap_two(summary), wrap_two(abstract)
    print(
        f"标题:{title}.\n")
    # 将文本写入文件
    inFoFile.write(
        f'# {title}.\n'
        f'<b>{summary}</b>\n\n'
        f'[摘要]'
        f'\n{abstract}\n\n'
        f'[文章链接]\n{link}\n\n'
        f'[发布时间]  \n{pub_time}\n\n'
        f'***\n\n'
    )
    # inFoFile.flush()


# 获取文章摘要
def get_abstract(url: str, all_result: dict):
    html = get_html(url, rand=useRandomHeaders, re_try_times=2)
    soup = BeautifulSoup(html, "lxml")
    # 去除页面无用标签
    [s.extract() for s in soup.find_all(attrs={'class': 'recommended pull pull--left u-sans-serif'})]

    text = soup.find(attrs={'class': 'c-article-body main-content'})
    text = str(text)
    # 内容排版
    text = text.replace('<h2>', '\n### ').replace('</h2>', '\n').replace('\n</figure>', '</figure>\n\n') \
        .replace('<figure class="figure">\n', '\n<figure class="figure">').replace('\n</figcaption>', '</figcaption>')
    text = re.sub(
        r'(</?a.*?>)|(</?p.*?>)|(<article.*?</article>)|(</source>)|(</?div.*?>)|(</?span.*?>)',
        '',
        text)

    all_result['abstract'] = text
    process_and_write(all_result)


def process_text_analysis(tag):
    try:
        # 文本处理
        # 标题
        title_link = tag.find(attrs={"class": "c-card__link u-link-inherit"})
        title = re.sub('(</?a.*?>)|(</?p>)', '', str(title_link))
        # 简介
        # 有些项无简介但有正文所以加入判断
        summary = tag.find(attrs={"class": "c-card__summary u-mb-16 u-hide-sm-max"})
        if summary is not None:
            summary = summary.select('p')[0]
            summary = re.sub('(</?a.*?>)|(</?p>)', '', str(summary))
        else:
            summary = 'None'
        # 文章链接'a'标签 用于转到正文页面进行爬取
        link = title_link.get('href')
        # 文章发布时间
        pub_time = tag.select("time[class='c-meta__item']")
        if pub_time is not None:
            pub_time = pub_time[0].get_text()
        else:
            pub_time = tag.select("time[class='c-meta__item c-meta__item--block-at-lg']")
            pub_time = pub_time[0].get_text()
        # 输出处理后文本
        if title is not None:
            # 获取摘要
            url = 'https://www.nature.com'
            url = url + link
            # 元素去重
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
            if url_hash in urlCollect:
                return
            else:
                urlCollect.add(url_hash)
            result = {
                'title': title, 'summary': summary,
                'pub_time': pub_time,
                'link': url
            }
            work_pool.submit(get_abstract, url, result)
        else:
            pass
    except Exception as e:
        print('\r\nprocess_text_analysis:  ' + str(e), end='')


# BeautifulSoup 处理HTML以提取信息
def start_text_analysis(soup: BeautifulSoup):
    start = time.perf_counter()
    # 获取每个文本盒子
    all_boxs = ['"app-featured-row__item"', '"app-news-row__item"',
                '"app-reviews-row__item"']
    for box in all_boxs:
        for tag in soup.select(f'li[class={box}]'):
            process_text_analysis(tag)
    work_pool.shutdown(wait=True)
    end = time.perf_counter()
    print(f'\r\nAnalysis completed in:  {end - start}s')


# 彩蛋功能的选取
def tt_draw(tt_type=0):
    if tt_type == 0:
        draw_random = Thread(target=tt_draw_random, daemon=True)
        draw_random.start()
    elif tt_type == 1:
        draw_polyhedral = Thread(target=tt_draw_polyhedral, daemon=True)
        draw_polyhedral.start()
    elif tt_type == 2:
        args_picture = ('https://www.yxlumen.com.cn/saveFiles/chicken_so_beautiful.png', 5, 0.5, 0.5)
        draw_picture = Thread(target=tt_draw_picture, args=args_picture)
        draw_picture.start()
    else:
        print('你干嘛,哎哟')


# 获取ip属地以推测用户地址（没什么用）
def get_ip_address():
    url = 'https://2023.ip138.com//'
    try:
        html = get_html(url, do_re_try=False)
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
        print('get_ip_address:  ' + str(e), end='')


# 写入配置文件
def json_api_write(fdir: str, api_id: str, secret_key: str):
    if not os.path.exists(fdir):
        os.mkdir(fdir)
    # 使用json库
    with open(fr'{fdir}\api.json', 'w') as f:
        api_dict = {"api_id": api_id, "secret_key": secret_key}
        json.dump(api_dict, f, indent=4, ensure_ascii=False)


# 读取配置文件
def json_api_read(file_path: str):
    # 文件是否可读
    if not os.access(file_path, os.R_OK):
        return None
    # 读取json
    with open(f'{file_path}', 'r') as f:
        ini = json.load(f)
    return ini


# Main function
def main():
    url_n = 'https://www.nature.com/'
    global useRandomHeaders
    useRandomHeaders = input('(y/n)是否使用随机请求头:  ')

    if useRandomHeaders == 'n':
        useRandomHeaders = False
    else:
        print('已选择随机请求头')
        useRandomHeaders = True

    print('开始爬取\n' + '——' * 30)
    html_nature = get_html(url_n, rand=useRandomHeaders)

    try:
        soup_main = BeautifulSoup(html_nature, "lxml")
    except Exception as e:
        print('\r\nBs4:  ' + str(e), end='')
        exit('\r\n链接超时')
    if web_change(soup_main):
        print('请求完成,正在解析文档')
        start_text_analysis(soup_main)


# 程序开始
# __name__ == '__main__' 表示程序入口,如是直接运行此脚本则加载
if __name__ == '__main__':
    # 欢迎语句
    address = get_ip_address()
    if address is not None:
        print(f'你好，来自{address}的用户')

    # 配置文件地址
    folderDir = os.environ['APPDATA']
    fileName = 'api.json'
    path = folderDir + '\\pyhttpRe\\'
    # 定义可重入锁
    translateLock = RLock()
    # 定义集合,用于后续重复元素去除
    urlCollect = set()
    # fake_useragent 应用外部数据设置
    useExternalData = True
    # 随机请求头
    useRandomHeaders = False
    # Treading
    work_pool = ThreadPoolExecutor(max_workers=8)

    while True:
        # 选择
        select = input('\n(1)获取;(2)强制刷新;(3)重新输入密钥;(4)查询当前密钥;(5)清除密钥;(q)退出\r\n')
        # 预处理和后处理
        if select == '1':
            if not os.path.exists('save files'):
                os.mkdir('save files')
            # 打开文档流
            inFoFile = codecs.open("./save files/temp-Nature.txt", 'w+', 'utf-8')
            inFoFile.write("")
            # 主函数
            select = input('(y/n)是否翻译?:  ')
            main()
            # 关闭文档流
            inFoFile.close()
            date = time.strftime('%y-%m-%d')

            # 清除字符
            if os.path.getsize('./save files/temp-Nature.txt'):
                change_character_doc('./save files/temp-Nature.txt', f'./save files/{date}-Nature.md')

            print(f'爬取完成,结果保存于{date}-Nature.md')
            os.remove('./save files/temp-Nature.txt')
        # 重置 页面 Hash
        elif select == '2':
            try:
                os.unlink('save files/hash.json')
                print('刷新完成')
            except FileNotFoundError:
                print('无此文件')
        # 重置配置
        elif select == '3':
            apiId = input('API账户: ')
            secretKey = input('API密钥: ')
            json_api_write(path, apiId, secretKey)
        # 查看配置
        elif select == '4':
            api = json_api_read(path + 'api.json')
            if api is not None:
                print(f'API账户: {api["api_id"]}\nAPI密钥: {api["secret_key"]}')
            else:
                print('无密钥文件')
        # 删除配置
        elif select == '5':
            a = input('确认清除?  y/n\n')
            if a == 'y':
                try:
                    os.remove(path + 'api.json')
                except FileNotFoundError:
                    print('无配置文件')
        # 彩蛋功能
        elif select[0:2] == 'tt':
            if len(select) > 2:
                ttType = select[-1]
                tt_draw(int(ttType))
            else:
                tt_draw()
        # 退出
        elif select == 'q':
            break

        else:
            print('无此选项')

    print('主进程退出')
