import requests
from bs4 import BeautifulSoup
import logging
from jieba.analyse import extract_tags
import logstash
import time
import random
import pymongo
from pymongo.errors import BulkWriteError
import jieba
import re
from Mongo_account import MongoBase
from concurrent.futures import ThreadPoolExecutor, as_completed

host = '10.120.14.105'
client = "mongodb://" + host + ":27017/"
# 多執行續下 可能被 dead lock
myclient = pymongo.MongoClient(client,
                               username=MongoBase.username,
                               password=MongoBase.password,
                               authSource=MongoBase.authSource,
                               authMechanism=MongoBase.authMechanism,
                               connect=False)
# 選擇 DB
mydb = myclient["cb104_G3"]
# 選擇 collection
mycol = mydb["ptt_fix"]

jieba.load_userdict("dict.txt.big")

proxylist = [{"http": "37.187.120.123:80"},
             {"https": "178.128.31.153:8080"},
             {"http": "167.114.180.102:8080"},
             {"https": "218.48.229.153:808"},
             {"http": "85.30.219.120:46761"},
             {"http": "183.101.103.164:8080"},
             {"http": "167.114.196.153:80"},
             {"http": "220.132.207.11:45069"}]
header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}


logger = logging.getLogger('python-logstash-logger')
logger.setLevel(logging.INFO)
logger.addHandler(logstash.TCPLogstashHandler(host, 5959))


def get_url(n=2, m=3):
    result = []
    # 增加直覺 從第n頁 到 第m頁
    m = m + 1
    for t in range(n, m):
        url = "https://www.ptt.cc/bbs/Food/index" + str(t) + ".html"
        result.append(url)
    return result


# slove proxy connect error try next
def get_connect(url):
    i = random.randint(0, len(proxylist) - 1)
    while True:
        try:
            resp = requests.get(url, headers=header, proxies=proxylist[i], timeout=120)
            resp.encoding = "utf-8"
            time.sleep(random.randint(1, 10) / 10)
            logger.info("Request response", exc_info=True,
                        extra={"url": url, "time_use": resp.elapsed.total_seconds(), "Response code": resp.status_code,
                               "proxy_use": proxylist[i]})
        except requests.exceptions.ConnectTimeout:
            logger.warning("Connect Time out", exc_info=True)
            i = (i + 1) % len(proxylist)
            continue

        except requests.exceptions.ConnectionError:
            logger.warning("Proxy Error", exc_info=True, extra={"proxy": proxylist[i], "url": url})
            i = (i + 1) % len(proxylist)
            continue

        if resp.status_code == requests.codes.ok:
            code = "HTTP response code = " + str(resp.status_code)
            logger.info(code, exc_info=True, extra={"url": url})

            break
        if resp.status_code == 404:
            logger.warning("This page is gone nowhere !", exc_info=True, extra={"url": url})

            break
        i = i + 1

    return resp


# 自定義 404 connectError
class Connect404Except(Exception):
    pass


def parse(urls):
    # 進入ptt列表 抓取 標題、推文數、網址
    result = []
    start = time.time()
    logger.info("getting connect...", exc_info=True)
    connect = get_connect(urls)
    soup = ""
    try:
        if connect.status_code == 404:
            raise Connect404Except

        else:
            soup = BeautifulSoup(connect.text)

    except Connect404Except:
        logger.error("index error", exc_info=True, extra={"index": urls})
        pass
    end_index = time.time()
    logger.info("index request complete", exc_info=True, extra={"time_use": end_index - start})
    if soup:
        print("進入ptt : ", urls)
        post = soup.find_all("div", class_="r-ent")

        for r in post:

            push = 0
            if r.find("div", class_="nrec").text:

                try:
                    push = int(r.find("div", class_="nrec").text)
                except ValueError:

                    pass
            if r.find("a"):
                # 取得網址
                href = "http://www.ptt.cc" + r.find("a")["href"]
                # 取得標題
                title = r.find("a").text

                # 進入第二層 進入每一篇
                # 去除公告 請益 為分類的文章
                if "公告" in title:
                    continue
                elif "問卷" in title:
                    continue
                else:
                    print("現在處理: ", href)
                    logger.info("getting connect...", exc_info=True)
                    article = get_connect(href)
                    try:
                        if article.status_code == 404:
                            raise Connect404Except
                        else:
                            art = BeautifulSoup(article.text)

                    except Connect404Except:
                        logger.error("Page error", exc_info=True, extra={"url": href, "index": urls})
                        continue

                    end_post_request = time.time()
                    logger.info("post request complete", exc_info=True,
                                extra={"time_use": end_post_request - end_index})
                    time.sleep(random.randint(1, 10) / 10)

                    if art:
                        content = art.find("div", id="main-content")

                        # 保存要丟棄的資訊
                        val = content.find_all("span", {"class": "article-meta-value"})
                        #  文章排版問題 有些文章沒有部份以下資訊
                        try:
                            author = val[0].text

                            date_in_content = val[3].text
                        except IndexError:
                            logger.warning("article span list out of index", exc_info=True, extra={"url": href})
                            author = ""
                            date_in_content = ""

                        # 開始丟棄資訊
                        removes = content.find_all("div", class_="article-metaline")
                        for remove in removes:
                            remove.extract()
                        removes = content.find_all("div", class_="article-metaline-right")
                        for remove in removes:
                            remove.extract()
                        removes = content.find_all("span", class_="f6")
                        for remove in removes:
                            remove.extract()
                        removes = content.find_all("span", class_="f2")
                        for remove in removes:
                            if "※" in remove.text:
                                remove.extract()
                        # 處理推噓文
                        ps = content.find_all("div", class_="push")
                        score = 0
                        pos = []
                        neg = []
                        arrow = []
                        if ps:
                            for p in ps:
                                tag = p.find("span", class_="push-tag").text
                                if "推" in tag:
                                    score = score + 1
                                    # replace 第三個參數 只置換第一個
                                    # push_content = p.find("span", class_="push-content").text.replace(": ","",1)
                                    push_content = p.find("span", class_="push-content").text
                                    push_ID = p.find("span", class_="push-userid").text
                                    push_total = push_ID + push_content
                                    pos.append(push_total)
                                elif "噓" in tag:
                                    score = score - 1
                                    push_content = p.find("span", class_="push-content").text
                                    push_ID = p.find("span", class_="push-userid").text
                                    push_total = push_ID + push_content
                                    neg.append(push_total)
                                else:
                                    push_content = p.find("span", class_="push-content").text
                                    push_ID = p.find("span", class_="push-userid").text
                                    push_total = push_ID + push_content
                                    arrow.append(push_total)
                                p.extract()

                        try:
                            content = content.text.replace("\r", "").replace("\n", "").replace(" ", "")
                        except AttributeError:
                            logger.warning("content text cant regularize", exc_info=True, extra={"url": href})

                        result.append({
                            "title": title,
                            "author": author,
                            "date": date_in_content,
                            "push": push,
                            "href": href,
                            "content": content,
                            "score": score,
                            "推文": pos,
                            "噓文": neg,
                            "箭頭": arrow,
                            "tags": extract_tags(content, 10)

                        })
                        end_post = time.time()
                        logger.info("post complete", exc_info=True, extra={"time_use": end_post - end_post_request})

        # 進入 db
        try:
            end_all = time.time() - start
            # insert many ordered = false -> collection中有 唯一鍵值 若遇上duplicate 則跳過
            x = mycol.insert_many(result, ordered=False)
            if x.inserted_ids:
                logger.info("Insert Successful", exc_info=True,
                            extra={"count": len(x.inserted_ids), "index_url": urls, "time_use": end_all})

        except BulkWriteError as e:
            for excep in e.details['writeErrors']:
                logger.warning("DB error", exc_info=True, extra={"error_detail": excep["errmsg"], "index_url": urls})

    return result


def main(n, m):
    with ThreadPoolExecutor(max_workers=30, thread_name_prefix="ptt_crawler") as executor:
        future_result = {executor.submit(parse, url): url for url in get_url(n, m)}
    for future in as_completed(future_result):
        logger.info("Worker's job done", exc_info=True)


if __name__ == "__main__":
    main(2,7002)