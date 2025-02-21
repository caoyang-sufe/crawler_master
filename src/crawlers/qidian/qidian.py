# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import re
import time
import json
import random
import pandas
import logging
import requests
from copy import deepcopy
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urljoin
from datetime import datetime, timedelta

from src.crawlers.base import BaseCrawler
from src.crawlers.qidian import CRAWLER_NAME

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class QidianCrawler(BaseCrawler):
	url_host = "https://www.qidian.com/"
	headers = {
		"chrome": """Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: max-age=0
Connection: keep-alive
Cookie: newstatisticUUID=1735736665_1330287369; fu=1411148269; _gid=GA1.2.311151734.1735736665; supportwebp=true; supportWebp=true; traffic_search_engine=; e1=%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A3%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_p_qidian%22%2C%22eid%22%3A%22qd_A18%22%7D; e2=%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A3%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_p_qidian%22%2C%22eid%22%3A%22qd_A71%22%7D; _csrfToken=wJZ2lZ7HlpYirfBKTrIuscc4mVnNOFE1SFVzedBu; Hm_lvt_f00f67093ce2f38f215010b699629083=1735736665,1735738442; HMACCOUNT=A940353C78CE7888; se_ref=; _ga_FZMMH98S83=GS1.1.1735741481.2.0.1735741481.0.0.0; _ga_PFYW0QLV3P=GS1.1.1735741481.2.0.1735741481.0.0.0; x-waf-captcha-referer=; Hm_lpvt_f00f67093ce2f38f215010b699629083=1735786018; traffic_utm_referer=; _ga=GA1.2.139609715.1735736665; _gat_gtag_UA_199934072_2=1; w_tsfp=ltvuV0MF2utBvS0Q6q/unE2uFz8lczE4h0wpEaR0f5thQLErU5mG1IFyuMv1N3La4sxnvd7DsZoyJTLYCJI3dwMTQ8uQJYgWhFiZktMt2dsQUBBgEJyPX1FJIe9zv2RDKHhCNxS00jA8eIUd379yilkMsyN1zap3TO14fstJ019E6KDQmI5uDW3HlFWQRzaLbjcMcuqPr6g18L5a5W7ZsVz+Kw4iArlHhhCahnsZWiwms0W7JuwIME2kIc39SqA=
Host: www.qidian.com
Referer: https://www.qidian.com/chapter/1041884414/807844618/
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
sec-ch-ua: "Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: \"Windows\"""",
	}

	def __init__(self,
				 **kwargs,
				 ):
		super(QidianCrawler, self).__init__(**kwargs)
		self.regexes["html_tag"] = re.compile(r"<[^>]+>|\t")	# Remove HTML tags, including '\t' only
		self.download_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "download")	# Save the downloaded data
		os.makedirs(self.download_dir, exist_ok=True)

	# Deal with keyword arguments `url` and `html`
	def _easy_soup(self, url, html):
		if html is None:
			assert url is not None, "Keyword arguments `url` and `html` are both NoneType!"
			html = self.easy_requests(
				method = "GET",
				url = url,
				max_trial = 5,
				headers = BaseCrawler.headers_to_dict(headers=self.headers["chrome"]),
				timeout = 30,
			).text
		return BeautifulSoup(html, "lxml")

	# 2025/01/16 21:05:14 Currently the `href` of chapter like `//www.qidian.com/chapter/1041884414/807844618/`
	def _process_chapter_href(self, href):
		if href.startswith("//www.qidian.com"):
			return f"https:{href}"
		elif href.startswith("/chapter"):
			return f"https://www.qidian.com{href}"
		else:
			raise Exception(f"Unknown chapter URL: {href}")

	# @param url: Book URL, e.g. https://www.qidian.com/book/1041884414/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return book_info: Dict[bookName[Str], meta[Str], intro[Str], count[Str]]
	def parse_book_info(self, url = None, html = None):
		soup = self._easy_soup(url, html)
		div_book_info = soup.find("div", class_="book-info")
		book_name = self.regexes["html_tag"].sub(str(), str(div_book_info.find("h1", id="bookName")))
		meta = self.regexes["html_tag"].sub(str(), str(div_book_info.find('p', class_="book-meta")))
		intro = self.regexes["html_tag"].sub(str(), str(div_book_info.find('p', class_="intro")))
		count = self.regexes["html_tag"].sub(str(), str(div_book_info.find('p', class_="count")))
		return {"bookName": book_name, "meta": meta, "intro": intro, "count": count}

	# @param url: Book URL, e.g. https://www.qidian.com/book/1041884414/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return book_catalog: List[Dict[volumeName[Str], isFree[Boolean], chapters[List[Dict[chapterName[Str], chapterURL[Str]]]]]]
	def parse_book_catalog(self, url = None, html = None):
		soup = self._easy_soup(url, html)
		div_catalog_volumes = soup.find_all("div", class_="catalog-volume")	# Catalog Volumes are not unique
		book_catalog = list()
		for div_catalog_volume in div_catalog_volumes:
			# Tranverse each volume of book
			label = div_catalog_volume.find("label")
			volume_name = self.regexes["html_tag"].sub(str(), str(label))
			logging.info(f"Volume Name: {volume_name}")
			is_free = label.find("span", class_="free") is not None
			ul_volume_chapters = div_catalog_volume.find("ul", class_="volume-chapters")
			li_chapter_items = ul_volume_chapters.find_all("li", class_="chapter-item")
			volumn_catalog = {"volumeName": volume_name, "isFree": is_free, "chapters": list()}
			for li_chapter_item in li_chapter_items:
				# Tranverse each chapter in 
				a_chapter_name = li_chapter_item.find('a', class_="chapter-name")
				chapter_name = self.regexes["html_tag"].sub(str(), str(a_chapter_name))
				chapter_url = self._process_chapter_href(a_chapter_name.attrs["href"])
				volumn_catalog["chapters"].append({"chapterName": chapter_name, "chapterURL": chapter_url})
			book_catalog.append(volumn_catalog)
		return book_catalog

	# @param url: Chapter URL, e.g. https://www.qidian.com/chapter/1041884414/807844618/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return reader_content: Str
	def parse_reader_content(self, url = None, html = None):
		soup = self._easy_soup(url, html)
		reader_content = str()
		div_reader_content = soup.find("div", id="reader-content")
		for p_label in div_reader_content.find_all('p'):
			reader_content += self.regexes["html_tag"].sub(str(), str(p_label))
			reader_content += '\n'
		return reader_content

	# @param book_url: Book URL, e.g. https://www.qidian.com/book/1041884414/
	# @return book: Dict[info[@return book_info], catalog[@return book_catalog], content[List[List[Dict[title[Str], text[Str]]]]]]
	def parse_book(self, book_url, save_dir = None, interval = 1):
		book_id = book_url.rstrip('/').split('/')[-1]
		save_dir = self.download_dir if save_dir is None else save_dir
		html = self.easy_requests(
			method = "GET",
			url = book_url,
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["chrome"]),
			timeout = 30,
		).text
		
		logging.info("Parsing book info and catalog ...")
		book_info = self.parse_book_info(url = None, html = html)
		book_catalog = self.parse_book_catalog(url = None, html = html)
		book = {
			"info": book_info,
			"catalog": book_catalog,
			"content": list(),
		}
		logging.info(f"Book name: {book_info['bookName']}")
		logging.info(f"Book meta: {book_info['meta']}")
		logging.info(f"Book intro: {book_info['intro']}")
		logging.info(f"Book count: {book_info['count']}")
		logging.info("Parsing chapter content ...")
		book_text = str()
		for i, volume_catalog in enumerate(book_catalog):
			volume_name = volume_catalog["volumeName"]
			is_free = volume_catalog["isFree"]
			chapters = volume_catalog["chapters"]
			volume_content = list()
			logging.info(f"Volume {i}:")
			logging.info(f"  - Name: {volume_name}")
			logging.info(f"  - Free: {is_free}")
			logging.info(f"  - Chapter #: {len(chapters)}")
			book_text += '=' * 64 + '\n'
			book_text += f"\n{volume_name}\n"
			for j, chapter in enumerate(chapters):
				chapter_name = chapter["chapterName"]
				chapter_url = chapter["chapterURL"]
				book_text += '-' * 64 + '\n'
				book_text += f"\n{chapter_name}\n"
				logging.info(f"  {j + 1}. {chapter_name}")
				reader_content = self.parse_reader_content(url = chapter_url, html = None)
				book_text += f"\n{reader_content}\n"
				volume_content.append({"title": chapter_name, "text": reader_content})
			book["content"].append(volume_content)
			time.sleep(interval)
		save_name = f"{book_id}-{book_info['bookName']}"
		with open(os.path.join(save_dir, f"{save_name}.json"), 'w', encoding="utf8") as f:
			json.dump(book, f, ensure_ascii=False)
		with open(os.path.join(save_dir, f"{save_name}.txt"), 'w', encoding="utf8") as f:
			f.write(book_text)
		return book

