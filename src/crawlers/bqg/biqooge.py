# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn
# General BiQuGe Crawler

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
from src.crawlers.bqg import CRAWLER_NAME

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class BQGCrawler(BaseCrawler):
	url_host = "https://www.bqg128.com/"
	headers = {
		"chrome": """accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
accept-encoding: gzip, deflate
accept-language: zh-CN,zh;q=0.9
cache-control: max-age=0
cookie: Hm_lvt_a4f729f0d035db225bffb944d51901aa=1737262848; HMACCOUNT=A940353C78CE7888; getsite=bq02.cc; hm=8a704070b913bd0cc6f2e7339cefa85f; hmt=1737262933; Hm_lpvt_a4f729f0d035db225bffb944d51901aa=1737262866
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-origin
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36""",
		"chrome": """accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
accept-encoding: gzip, deflate, br, zstd
accept-language: zh-CN,zh;q=0.9
cache-control: max-age=0
cookie: SITE_TOTAL_ID=0c3fca44157f896cad96f01bd2824229; Hm_lvt_2f12be9030b42d09e3e0a5de48a114d2=1767853005,1767880079; HMACCOUNT=775157CE17F9C131; Hm_lvt_405a34174b7d925aa7013663c57c4aae=1767853005,1767880079; ge_js_validator_20=1767880614@20@db13ae56fac1647e677c38bac3c0b26f; Hm_lpvt_405a34174b7d925aa7013663c57c4aae=1767880615; Hm_lpvt_2f12be9030b42d09e3e0a5de48a114d2=1767880615
sec-ch-ua: "Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-origin
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36""",
		"redirect": """accept: text/html
accept-encoding: gzip, deflate
accept-language: zh-CN,zh;q=0.9
cookie: Hm_lvt_a4f729f0d035db225bffb944d51901aa=1737262848; HMACCOUNT=A940353C78CE7888; getsite=bq02.cc; hm=8a704070b913bd0cc6f2e7339cefa85f; hmt=1737262933; goad=1; Hm_lpvt_a4f729f0d035db225bffb944d51901aa=1737264407
priority: u=0, i
sec-ch-ua: "Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-origin
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36""",
	}

	def __init__(self,
				 **kwargs,
				 ):
		super(BQGCrawler, self).__init__(**kwargs)
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

	# 2025/01/16 21:05:14 Currently the `href` of chapter like `/book/17466/1.html`
	def _process_chapter_href(self, href):
		if href.startswith("javascript"):
			return None
		return urljoin(self.url_host, href)

	# @param url: Book URL, e.g. https://www.bqg128.com/book/97198/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return book_info: Dict[bookName[Str], meta[Str], intro[Str], count[Str]]
	def parse_book_info(self, url = None, html = None):
		soup = self._easy_soup(url, html)
		div_book_info = soup.find("div", class_="info")
		book_name = meta = intro = None
		try:
			book_name = self.regexes["html_tag"].sub(str(), str(div_book_info.find("h1")))
			meta = self.regexes["html_tag"].sub(str(), str(div_book_info.find('div', class_="small")))
			intro = self.regexes["html_tag"].sub(str(), str(div_book_info.find('div', class_="intro")))
		except:
			pass
		return {"bookName": book_name, "meta": meta, "intro": intro}

	# @param url: Book URL, e.g. https://www.bqg128.com/book/97198/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return book_catalog: List[Dict[chapterName[Str], chapterURL[Str]]]
	# * Note: There is no volume hierarchy and Free/VIP in BQG, so that the `book_catalog` is shallow (as to `QidianCrawler`)
	def parse_book_catalog(self, url = None, html = None):
		soup = self._easy_soup(url, html)
		dd_chapters = soup.find("div", class_="listmain").find_all("dd")	# Catalog Volumes are not unique
		# dd_chapters = soup.find("div", class_="chapter container").find_all("li")	# Catalog Volumes are not unique
		# dd_chapters = soup.find("div", class_="list").find_all("li")	# Catalog Volumes are not unique
		# dd_chapters = soup.find("ul", attrs={"class": "fix section-list"}).find_all("li")	# Catalog Volumes are not unique
		book_catalog = list()
		for dd_chapter in dd_chapters:
			# Tranverse each chapter
			a_chapter = dd_chapter.find('a')
			chapter_name = self.regexes["html_tag"].sub(str(), str(a_chapter))
			chapter_url = self._process_chapter_href(a_chapter.attrs["href"])
			if chapter_url is not None:
				book_catalog.append({"chapterName": chapter_name, "chapterURL": chapter_url})
		return book_catalog

	# @param url: Chapter URL, e.g. https://www.qidian.com/chapter/1041884414/807844618/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return reader_content: Str
	# 2025/01/19 13:33:56
	# - Redirection in biquge, `url` need to be used in request headers
	# - Otherwise, only part of the reader content is displayed
	def parse_reader_content(self, url):
		headers = BaseCrawler.headers_to_dict(headers=self.headers["redirect"])
		headers["Referer"] = url
		print(url)
		url = url.replace("bqg128.cc/book/171185", "bqg8140.cc/#/book/179803")
		print(url)
		# html = self.easy_requests(
			# method = "GET",
			# url = url,
			# max_trial = 5,
			# headers = BaseCrawler.headers_to_dict(headers=self.headers["chrome"]),
			# timeout = 30,
		# ).text
		html = self.get_page_source(
			url,
			driver = None,
			browser = "chrome",
		)
		print(html)
		soup = BeautifulSoup(html, "lxml")
		reader_content = str()
		div_reader_content = soup.find("div", id="chaptercontent")
		if div_reader_content is None:
			div_reader_content = soup.find("div", class_="content")
		if div_reader_content is None:
			div_reader_content = soup.find("article", class_="article")
		if div_reader_content is None:
			div_reader_content = soup.find("div", class_="word_read")
		if div_reader_content is None:
			print(div_reader_content)
			input("Reader Content is None!")
		reader_content = self.regexes["br"].sub('\n', str(div_reader_content))
		reader_content = self.regexes["html_tag"].sub(str(), reader_content)
		return reader_content
		肉块，人体内脏

	# @param book_url: Book URL, e.g. https://www.bqg4635.cc/#/book/46745/
	# @return book: Dict[info[@return book_info], catalog[@return book_catalog], content[List[List[Dict[title[Str], text[Str]]]]]]
	def parse_book(self, book_url, save_dir = None, interval = 1):
		self.url_host = '/'.join(book_url.split('/')[:3]) + '/'
		logging.info(f"Host URL: {self.url_host}")
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
		logging.info("Parsing chapter content ...")
		save_name = f"{book_id}-{book_info['bookName']}"
		save_path = os.path.join(save_dir, f"{save_name}.txt")
		with open(save_path, 'w', encoding="utf8") as f:
			pass
		for i, chapter in enumerate(book_catalog):
			buffer_text = str()
			chapter_name = chapter["chapterName"]
			chapter_url = chapter["chapterURL"]
			buffer_text += '-' * 64 + '\n'
			buffer_text += f"\n第{i + 1}章 {chapter_name}\n"
			logging.info(f"  {i + 1}. {chapter_name}")
			reader_content = self.parse_reader_content(url = chapter_url)
			buffer_text += f"\n{reader_content}\n"
			book["content"].append({"title": chapter_name, "text": reader_content})
			time.sleep(interval)
			with open(os.path.join(save_dir, f"{save_name}.txt"), 'a', encoding="utf8") as f:
				f.write(buffer_text)
		with open(os.path.join(save_dir, f"{save_name}.json"), 'w', encoding="utf8") as f:
			json.dump(book, f, ensure_ascii=False)
		return book

