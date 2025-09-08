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
from src.crawlers.bixia import CRAWLER_NAME

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class Bxwxx7Crawler(BaseCrawler):
	url_host = "https://www.bxwxx7.com/"
	url_summary = {
	}
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
	}

	def __init__(self,
				 **kwargs,
				 ):
		super(Bxwxx7Crawler, self).__init__(**kwargs)
		self.regexes["html_tag"] = re.compile(r"<[^>]+>|\t")	# Remove HTML tags, including '\t' only
		self.regexes["p_tag"] = re.compile(r"<p>|<p/>")	# Replace <p> by '\n'
		self.download_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "download")	# Save the downloaded data
		os.makedirs(self.download_dir, exist_ok=True)


	# @param url: Book URL, e.g. https://www.bxwxx7.com/article/233061/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return book_info: Dict[bookName[Str], meta[Str], intro[Str], count[Str]]
	def parse_book_info(self, url = None, html = None):
		soup = self._easy_soup(url, html)
		div_book_info = soup.find("div", id="maininfo")
		book_name = self.regexes["html_tag"].sub(str(), str(div_book_info.find("div", id="info").find("h1")))
		meta = self.regexes["html_tag"].sub(str(), str(div_book_info))
		intro = self.regexes["html_tag"].sub(str(), str(soup.find("div", class_="intro")))
		return {"bookName": book_name, "meta": meta, "intro": intro}

	# @param url: Book URL, e.g. https://www.bqg128.com/book/97198/
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return book_catalog: List[Dict[chapterName[Str], chapterURL[Str]]]
	# * Note: There is no volume hierarchy and Free/VIP in BQG, so that the `book_catalog` is shallow (as to `QidianCrawler`)
	def parse_book_catalog(self, url = None, html = None):
		soup = self._easy_soup(url, html)
		dd_chapters = soup.find("dl", id="newlist").find_all("dd")	# Catalog Volumes are not unique
		book_catalog = list()
		for dd_chapter in dd_chapters:
			# Tranverse each chapter
			a_chapter = dd_chapter.find('a')
			chapter_name = self.regexes["html_tag"].sub(str(), str(a_chapter))
			if "href" in a_chapter.attrs:
				chapter_url = a_chapter.attrs["href"]
			else:
				chapter_url = None
			book_catalog.append({"chapterName": chapter_name, "chapterURL": chapter_url})
		return book_catalog

	# @param url: Chapter URL, e.g. https://www.bxwxx7.com/article/122858/54915953.html
	# @param html: HTML extracted from `url`, either `url` or `html` is NoneType
	# @return reader_content: Str
	# @return next_chapter_url: Str, URL referring to the next chapter in case NaN
	# 2025/01/19 13:33:56
	# - Redirection in biquge, `url` need to be used in request headers
	# - Otherwise, only part of the reader content is displayed
	def parse_reader_content(self, url):
		reader_content = str()
		next_page_url = url
		page_no = 0
		while True:
			page_no += 1
			logging.info(f"    第 {page_no}页：{next_page_url}")
			# In Biquge, one chapter contains only one page
			# In Bixia, one chapter may contain several pages, we need to check tag `<a rel="next">`
			html = self.easy_requests(
				method = "GET",
				url = urljoin(self.url_host, next_page_url),
				max_trial = 5,
				headers = BaseCrawler.headers_to_dict(headers=self.headers["chrome"]),
				timeout = 30,
			).text
			soup = BeautifulSoup(html, "lxml")
			next_page_tag = soup.find('a', attrs={"rel": "next"})
			next_page_text = self.regexes["html_tag"].sub(str(), str(next_page_tag))
			if next_page_text == "下一页":
				next_page_flag = True
			elif next_page_text == "下一章":
				next_page_flag = False
			elif next_page_text == "无下章":
				next_page_flag = False
			else:
				logging.warning(f"Unknown `next_page_text`: {next_page_text}")
				next_page_flag = False
			div_reader_content = soup.find("div", id="booktxt")
			if div_reader_content is None:
				div_reader_content = soup.find("div", id="chaptercontent")
			page_content = self.regexes["br"].sub('\n', str(div_reader_content))
			page_content = self.regexes["p_tag"].sub('\n', page_content)
			page_content = self.regexes["html_tag"].sub(str(), page_content)
			reader_content += page_content + '\n' * 2
			if next_page_flag:
				next_page_url = next_page_tag.attrs["href"]
			else:
				next_chapter_url = next_page_tag.attrs["href"]
				return reader_content, next_chapter_url

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
		logging.info("Parsing chapter content ...")
		book_text = str()
		next_chapter_url = None
		for i, chapter in enumerate(book_catalog):
			chapter_name = chapter["chapterName"]
			chapter_url = chapter["chapterURL"]
			if chapter_url is None:
				chapter_url = next_chapter_url
			book_text += '-' * 64 + '\n'
			book_text += f"\n第{i + 1}章 {chapter_name}\n"
			logging.info(f"  {i + 1}. {chapter_name}")
			reader_content, next_chapter_url = self.parse_reader_content(url = chapter_url)
			book_text += f"\n{reader_content}\n"
			book["content"].append({"title": chapter_name, "text": reader_content})
			time.sleep(interval)
		save_name_txt = f"{book_id}-{book_info['bookName']}"
		save_name_json = f"{book_id}"
		with open(os.path.join(save_dir, f"{save_name_txt}.txt"), 'w', encoding="utf8") as f:
			f.write(book_text)
		with open(os.path.join(save_dir, f"{save_name_json}.json"), 'w', encoding="utf8") as f:
			json.dump(book, f, ensure_ascii=False)
		return book

