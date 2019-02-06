# use in crawler
import requests
from bs4 import BeautifulSoup


def get_pixnet_content(url):

    # 傳入 經過BeautifulSoup 處理的 soup
    # 若出現亂碼情況 請在requests.get()之後
    # 加入encoding = 'utf-8'
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    pixnet_content = soup.find("div", id="article-content-inner")
    removes = pixnet_content.find_all("script")
    for remove in removes:
        remove.extract()

    removes = pixnet_content.find_all("ins")
    for remove in removes:
        remove.extract()

    removes = pixnet_content.find_all("a")
    for remove in removes:
        remove.extract()

    pixnet_content = re.sub(r"\W+", "", pixnet_content.text)

    return pixnet_content


def get_pixnet_image_urls(url):

    # 傳入 BeautifulSoup 處理後的 soup

    # 此方法回傳 Urls List
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    pixnet_content = soup.find("div", id="article-content-inner")
    images_url = []
    pattern = r"http\://farm2*"
    images = pixnet_content.find_all("img")
    for image in images:
        if re.match(pattern, image["src"]):
            images_url.append(image["src"])

    return images_url


def get_candicecity_content(url):

    # 傳入 經過BeautifulSoup 處理的 soup
    # 若出現亂碼情況 請在requests.get()之後
    # 加入encoding = 'utf-8'
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", class_="entry-content")
    clean_content = ""
    removes = content.find_all("ins")
    for remove in removes:
        remove.extract()
    removes = content.find_all("script")
    for remove in removes:
        remove.extract()

    content_p = content.find_all("p")
    for p in content_p:
        if ">>>" in p.text:
            pass
        elif "►" in p.text:
            pass
        elif "★" in p.text:
            pass
        elif "◆" in p.text:
            pass
        elif "▼" in p.text:
            pass
        elif "↓" in p.text:
            pass
        else:
            clean_content = clean_content + p.text

    clean_content = re.sub(r"\W+", "", clean_content)
    return clean_content


def get_candicecity_images_url(url):
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", class_="entry-content")
    pattern = r"//candicecity*"
    images_url = []
    images = content.find_all("img")
    for image in images:
        if re.match(pattern, image["src"]):
            images_url.append("https:"+image["src"])

    return images_url


def get_lanlan_content(url):
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", class_="entry-content")
    removes = content.find_all("script")
    for remove in removes:
        remove.extract()

    removes = content.find_all("ins")
    for remove in removes:
        remove.extract()

    removes = content.find_all("a")
    for remove in removes:
        remove.extract()

    content = re.sub(r"\W+", "", content.text)
    return content


def get_lanlan_images_url(url):
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    pattern = r"https?\://image\.lanlan\.tw/[^emotion]"
    content = soup.find("div", class_="entry-content")
    images = content.find_all("img")
    images_url = []
    for image in images:
        if re.match(pattern, image["src"]):
            images_url.append(image["src"])

    return images_url


def get_vivawei_content(url):
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", class_="desc")
    removes = content.find_all("script")
    for remove in removes:
        remove.extract()

    removes = content.find_all("ins")
    for remove in removes:
        remove.extract()

    removes = content.find_all("a")
    for remove in removes:
        remove.extract()

    content = re.sub(r"\W+", "", content.text)

    return content


def get_vivawei_images_url(url):
    import re
    resp = requests.get(url=url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", class_="desc")
    images = content.find_all("img")
    images_url = []
    for image in images:
        if re.match(r"https?", image["src"]):
            images_url.append(image["src"])
        else:
            images_url.append("https:" + image["src"])

    return images_url
