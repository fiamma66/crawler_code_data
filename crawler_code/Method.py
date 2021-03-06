# use in crawler
import requests
from bs4 import BeautifulSoup


def get_pixnet_content(url, headers=None):

    # 傳入 經過BeautifulSoup 處理的 soup
    # 若出現亂碼情況 請在requests.get()之後
    # 加入encoding = 'utf-8'
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
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


def get_pixnet_image_urls(url, headers=None):

    # 傳入 BeautifulSoup 處理後的 soup
    import re
    # 此方法回傳 Urls List

    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    pixnet_content = soup.find("div", id="article-content-inner")
    images_url = []
    pattern = r"(jpg)$"
    images = pixnet_content.find_all("img")
    for image in images:
        if re.search(pattern,image["src"]):
           images_url.append(image["src"])

    return images_url


def get_candicecity_content(url, headers=None):

    # 傳入 經過BeautifulSoup 處理的 soup
    # 若出現亂碼情況 請在requests.get()之後
    # 加入encoding = 'utf-8'
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
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


def get_candicecity_images_url(url, headers=None):
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", class_="entry-content")
    pattern = r"(jpg)$"
    images_url = []
    images = content.find_all("img")
    for image in images:
        if re.search(pattern, image["src"]):
            images_url.append("https:"+image["src"])

    return images_url


def get_lanlan_content(url, headers=None):
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
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


def get_lanlan_images_url(url, headers=None):
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    pattern = r"(jpg)$"
    content = soup.find("div", class_="entry-content")
    images = content.find_all("img")
    images_url = []
    for image in images:
        if re.search(pattern, image["src"]):
            images_url.append(image["src"])

    return images_url


def get_vivawei_content(url, headers=None):
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
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


def get_vivawei_images_url(url, headers=None):
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
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


def get_maiimage_content(url, headers=None):
    import re
    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", id="zi_ad_article_inread")
    removes = content.find_all("ins")
    for remove in removes:
        remove.extract()

    removes = content.find_all("a")
    for remove in removes:
        remove.extract()

    content = re.sub(r"\W+", "", content.text)

    return content


def get_maiimage_images_url(url, headers=None):

    if headers is None:
        resp = requests.get(url=url)
    else:
        resp = requests.get(url=url, headers=headers)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text)
    content = soup.find("div", id="zi_ad_article_inread")
    images_url = []
    images = content.find_all("img")
    for image in images:
        images_url.append("https:" + image["src"])

    return images_url
