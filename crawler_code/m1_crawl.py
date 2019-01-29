import requests
from bs4 import BeautifulSoup
import time
import re
import random
import logstash
import logging
import pymongo
from Mongo_account import MongoBase
from concurrent.futures import ThreadPoolExecutor, as_completed

from pymongo.errors import BulkWriteError
host = '10.120.14.105'
client = "mongodb://" + host + ":27017/"
# 多執行續下 可能被 dead lock
myclient = pymongo.MongoClient(client,
                               username= MongoBase.username,
                               password= MongoBase.password,
                               authSource= MongoBase.authSource,
                               authMechanism= MongoBase.authMechanism,
                               connect= False)
mydb = myclient["cb104_G3"]
mycol = mydb["Mobile01"]

logger = logging.getLogger('python-logstash-logger')
logger.setLevel(logging.INFO)

logger.addHandler(logstash.TCPLogstashHandler(host,5959))

def get_url(n=1, m=2):
    result = []
    # 增加直覺 從第n頁 到 第m頁
    m= m + 1
    for t in range(n, m):
        url= "https://www.mobile01.com/waypointlist.php?list=1&c=0&s=desc&pid=2&p=" + str(t)
        result.append(url)
    return result


proxylist= [{"http": "37.187.120.123:80"},
             {"https": "206.189.36.198:8080"},
             {"https": "178.128.31.153:8080"},
             {"http": "167.114.180.102:8080"},
             {"http": "104.131.214.218:80"},
             {"http": "167.114.196.153:80"}]
header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}


class Connect404Except(Exception):
    pass


# slove proxy connect error try next
def get_connect(url):
    i = random.randint(0, len(proxylist) - 1)

    while True:

        try:
            resp = requests.get(url, headers=header, proxies=proxylist[i], timeout=120)
            resp.encoding = "utf-8"
            time.sleep(random.randint(1, 10) / 10)
            logger.info("Request response", exc_info=True,extra={"url" : url, "time_use" : resp.elapsed.total_seconds(), "Response code" : resp.status_code, "proxy_use":proxylist[i]})

        except requests.exceptions.ConnectTimeout:
            logger.warning("Connect Time out", exc_info=True)
            i = (i + 1) % len(proxylist)
            continue

        except requests.exceptions.ConnectionError:
            logger.warning("Proxy Error", exc_info=True, extra={"proxy":proxylist[i],"url":url})

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


def get_res_info(soup):
    res_info = []
    info = soup.find(id="info_form")
    rate = 0
    phone = ""
    place = ""
    op_time = ""
    point = ""
    try:
        place = info.find_all("div")[1].text.replace("\n", "").replace(" ", "").split(":")[-1]
        phone = info.find_all("div")[2].text.replace("\n", "").replace(" ", "").split(":")[-1]
        op_time = info.find_all("div")[3].text.replace("\n", "").split("  ")[-1]
        point = info.find_all("div")[7].text.replace("\n", "").replace(" ", "").split(":")[-1]
        rate = len(info.find_all("div")[8].find_all("img"))
    except IndexError:
        logger.warning("Index wrong in this page",exc_info=True,extra={"url" : soup.find("meta", property = "og:url")["content"]})
        pass
    res_info.append({
        "rate": rate,
        "place": place,
        "phone": phone,
        "op_time": op_time,
        "point": point
    })
    return res_info


def get_comment_p2(soup):
    comment = []
    for single_comment in soup.find_all("article"):
        removes = single_comment.find_all("span", class_="poster")
        for remove in removes:
            remove.extract()
        removes = single_comment.find_all("blockquote")
        for remove in removes:
            remove.extract()
        author = single_comment.find("div", class_="single-post-author group").find("div", class_="fn").text
        content = single_comment.find("div", class_="single-post-content").text.replace("\n", "").replace("\r",
                                                                                                          "").replace(
            " ", "")
        content = author + ":" + content
        comment.append(content)

    return comment


def get_comment(soup):
    comment = []
    for single_comment in soup.find_all("article")[1:]:
        removes = single_comment.find_all("span", class_="poster")
        for remove in removes:
            remove.extract()
        removes = single_comment.find_all("blockquote")
        for remove in removes:
            remove.extract()
        author = single_comment.find("div", class_="single-post-author group").find("div", class_="fn").text
        content = single_comment.find("div", class_="single-post-content").text.replace("\n", "").replace("\r",
                                                                                                          "").replace(
            " ", "")
        content = author + ":" + content
        comment.append(content)
        while True:
            the_link = ""
            links = soup.find_all("div", class_="pagination")[1].find_all("a")
            for link in links:
                if link.find(string=re.compile("下一頁")):
                    the_link = "https://www.mobile01.com/" + link["href"]

            if the_link:
                # establish new connection
                conn = get_connect(the_link)
                try:
                    if conn.status_code == 404:
                        raise Connect404Except
                    else:
                        soup = BeautifulSoup(conn.text)
                except Connect404Except:
                    # logger.error("page error",extra={"url":the_link})
                    break
                # get our comment text
                if soup:
                    new_comment = get_comment_p2(soup)
                # append to comment list
                    for every_comment in new_comment:
                        comment.append(every_comment)
            else:
                break

    return comment


def parse(urls):
    result = []
    soup = ""
    connect = get_connect(urls)
    try:
        if connect.status_code == 404:
            raise Connect404Except

        else:
            soup = BeautifulSoup(connect.text)

    except Connect404Except:
        logger.error("index error", extra={"index": urls})
        pass

    if soup:
        print("進入", urls)
        table = soup.find_all("tr")
        # 取得列表內容
        for t in table:
            title = t.find("p", class_="title").text
            href = "https://www.mobile01.com/" + t.find("p", class_="title").find("a")["href"]
            sp = t.find("p", class_="info").text.split("-")[1].replace(" ", "")
            date = t.find("p", class_="info").text.split(":")[2].split(" ")[1]

            # 進入第二層 遊記 去除風景
            if "餐飲" in sp:
                print("現在處理:", href)
                conn = get_connect(href)
                try:

                    if conn.status_code == 404:
                        raise Connect404Except

                    else:
                        art = BeautifulSoup(conn.text)

                except Connect404Except:
                    logger.error("page error", extra={"url": href})
                    continue
                content = art.find("div", class_="single-post-content").text.replace("\r", "").replace("\n",
                                                                                                       "").replace(" ",
                                                                                                                   "")
                content = re.sub(r"\W+", "", content)
                img_url = []
                imgs = art.find("div", class_="single-post-content").find_all("img")
                for img in imgs:
                    img_url.append(img["data-src"])
                author = art.find("div", class_="panel note sidebar-authur").find("a").text
                article_hit = art.find_all("div", class_="panel note")[1].find_all("li")[0].text.split(":")[-1]
                rate = art.find_all("div", class_="panel note")[1].find_all("li")[1].text.split(":")[-1]
                res_info = get_res_info(art)
                # 進入第三層 評論
                comment_url = "https://www.mobile01.com/" + art.find("div", class_="btns wide").find("a")["href"]
                new_conn = get_connect(comment_url)
                comment = ""
                comment_art = ""
                try:
                    if new_conn.status_code == 404:
                        raise Connect404Except
                    else:
                        comment_art = BeautifulSoup(new_conn.text)
                except Connect404Except:
                    # logger.error("page error",extra={"url":comment_url})
                    pass
                if comment_art:
                    comment = get_comment(comment_art)

                # append all
                result.append({
                    "title": title,
                    "href": href,
                    "species": sp,
                    "date": date,
                    "content": content,
                    "img": img_url,
                    "author": author,
                    "article_hit": article_hit,
                    "rate": rate,
                    "info": res_info,
                    "comment": comment

                })
        try:
            x= mycol.insert_many(result, ordered= False)
            if x.inserted_ids:
                logger.info("Insert Successful", exc_info=True, extra={"count": len(x.inserted_ids), "index_url": urls})
        except BulkWriteError as e:
            for evey_except in e.details['writeErrors']:
                logger.warning("DB error",exc_info=True,extra={"error_detail":evey_except["errmsg"], "index_url" : urls})
    return result


def main(n, m):

    with ThreadPoolExecutor(max_workers=15) as executor:
        future_result = {executor.submit(parse, url): url for url in get_url(n, m)}
    for future in as_completed(future_result):
        logger.info("Jobs complete",exc_info=True)


if __name__ == "__main__":
    main(3,339)









