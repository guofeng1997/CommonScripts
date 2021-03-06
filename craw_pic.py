# coding=utf-8
"""
********  整站抓取图片,使用gevent+requests异步下载方式  ********
		*1.lxml包xpath工具获取url,其中xpath从chrome开发者工具获取
		*2.使requests下载
		*3.正则爬取url所有图片
		*4.协程处理图片下载任务
		*5.加入代理proxies
		*6.自动打开文件夹窗口展示图片

	requirements:
		- requests (2.11.1)
		- lxml (3.6.4)
		- gevent (1.1.2)
        	- tqdm (4.23.0)
"""
import re
import os
import time
import requests
from tqdm import tqdm
from lxml import etree
import gevent
from gevent import monkey


# --------创建路径,储存图片------------
BASEPATH = os.getcwd() + '/49vvpic/'
# http://qwx2.com/index.html # curl访问，用于获取ORIGIN_URL
ORIGIN_URL = 'http://www.gf3s.com/404.html?/'
# 使用socks5代理，可用其他vpn.先设置本地1080端口翻墙，然后设置requests的代理为该端口
PROXIES = dict(http='socks5://127.0.0.1:1080', https='socks5://127.0.0.1:1080')
TIMEOUT = 10  # 单位:秒


def get_urls(root_url, numth_url):
    res = requests.get(numth_url)
    selector = etree.HTML(res.content)
    # ------取中文标题------"
    pic_name = selector.xpath(
        "//*[@id='gotop']/div[2]/div/div/div[3]/div/ul/li/a/text()")
    pic = selector.xpath("//*[@id='gotop']/div[2]/div/div/div[3]/div/ul/li/a")
    # 将url名与对应的url进行打包
    urls = zip(pic_name, [root_url + node.attrib['href'] for node in pic])
    return (len(pic), urls)


def get_pic_url(url):  # 获取指定url下的所有图片url
    res = requests.get(url)
    # 图片所在标签: <a href=""><img src="" alt=""/></a></P>
    pic_urls = re.findall(
        '<a href=".*?"><img  src="(.*?)" alt=".*?" /></a></P>',
        res.text, re.S)  # 正则匹配
    # 每个网页最多下20张,因为很多重复的图片
    return pic_urls if len(pic_urls) <= 10 else pic_urls[:20]


def download(title, url, proxy_on=False):  # 图片下载
    if proxy_on:
        proxies = PROXIES
    else:
        proxies = {}
    url = re.sub('%2[eE]', '.', url, re.IGNORECASE)  # 如果.被编码为%2E则改回.
    res = requests.get(url, proxies=proxies, timeout=TIMEOUT)
    print('正在下载图片:' + url)
    name = re.split('\.|/+', url)
    filesavepath = title + name[-3] + str(time.time()) + '.' + name[-1]
    with open(filesavepath, 'wb') as f:  # 图片下载
        f.write(res.content)


def choose(root_url):
    """
        用户选择抓取的图片区
    """
    areas = ['asia', 'oumei', 'zipai', 'meitui', 'cartoon', '']
    while True:
        area = input(
            '亚洲:asia,欧美:oumei,自拍:zipai,美腿:meitui,动漫:cartoon\n爬取什么区? 请输入选项:')
        if area in areas:
            if area == '':  # 默认为亚洲区
                area = 'asia'
            break
        print('错误，请重新输入!')
    while True:
        number = input('爬取第几页?:')
        if number.isdigit():
            break
        print('错误，请重新输入!')

    # 首页index,第二页index-2,第三页index-3...
    number = '' if number == '1' or number == '' else '-' + number
    return root_url + 'AAtupian/AAtb/' + area + '/index' + number + '.html'


def do_work(BASEPATH, urls, proxy_on=False):
    urls_dict = dict(urls)
    for pic_name in tqdm(urls_dict):  # tqdm封装迭代器,显示进度
        title = BASEPATH + pic_name + '/'  # 根据标题,创建子目录,易于区分图集
        print("\n" + "-----------" * 6)
        try:
            print('\n开始下载:{0}, 图片数:{1}张'.format(
                pic_name, pic_name.split("P)")[0].split("(")[-1]))
        except Exception:
            pass
        pic_urls = get_pic_url(urls_dict[pic_name])  # 正则爬取图片url
        if not os.path.isdir(title) and len(pic_urls) > 0:
            os.mkdir(title)
        gevent.joinall([gevent.spawn(download, title, pic_url, proxy_on)
                        for pic_url in pic_urls])  # gevent并发下载
    print('\n下载完成!!')


def craw():
    try:
        # 从防黑页面获取root_url,防止网页挂掉
        r = requests.get(ORIGIN_URL, allow_redirects=True)
    except Exception as e:
        print('网络链接失败!请检查网络:{}\n'.format(e))
        exit(0)
    root_url = re.findall(
        '<div class="zhuli">.*?<a href=".*?">(.*?)</a>', r.text, re.S)
    print('root_url:', root_url)
    # 选择页面,第一页,第二页>..
    if not root_url:
        print('网页已挂，请更改ORIGIN_URL。')
        exit(0)     # 退出
    numth_url = choose(root_url[0])
    print("正在爬取:{}".format(numth_url))
    # 解决指定页有时返回0个url的情况
    while True:
        (numofurl, urls) = get_urls(root_url[0], numth_url)
        if numofurl != 0:
            break
    # 创建根目录
    if not os.path.isdir(BASEPATH):
        os.mkdir(BASEPATH)
        os.system('nautilus ' + BASEPATH)  # 打开文件夹图像窗口
    # 开始下载,开启代理
    do_work(BASEPATH, urls, True)


if __name__ == '__main__':
    monkey.patch_all()
    craw()
