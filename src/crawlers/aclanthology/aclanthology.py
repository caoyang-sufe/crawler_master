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

from src.crawlers.csdn import CRAWLER_NAME
from src.crawlers.base import BaseCrawler

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class ACLAnthologyCrawler(BaseCrawler):
	url_host = "https://aclanthology.org/"

	headers = {
		"paper_detail": """Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: max-age=0
Connection: keep-alive
Host: aclanthology.org
If-Modified-Since: Sun, 24 Nov 2024 17:47:17 GMT
If-None-Match: "75cb-627ac34fc1889-gzip"
Referer: https://aclanthology.org/events/acl-2024/
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
		super(ACLAnthologyCrawler, self).__init__(**kwargs)
		self.monitor_save_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "monitor")	# Save the monitor data
		os.makedirs(self.monitor_save_dir, exist_ok=True)

	# Parse paper details, e.g. title, authors, abstract, citation, bibtex, pdf
	# @param paper_id: Str, e.g. "2024.acl-long.1"
	def parse_paper_detail(self,
						   paper_id,
						   save_dir = "./",
						   download_bibtex = True,
						   download_pdf = True,
						   ):
		os.makedirs(save_dir, exist_ok=True)
		detail_dict = dict()
		url_paper_detail = urljoin(self.url_host, paper_id)
		headers_paper_detail = BaseCrawler.headers_to_dict(headers=self.headers["paper_detail"])
		response = self.easy_requests(method = "GET",
									  url = url_paper_detail,
									  max_trial = -1,
									  headers = headers_paper_detail,
									  timeout = 30,
									  )
		soup = BeautifulSoup(response.text, "lxml")
		# Title
		title_tag = soup.find("h2", id="title")
		title = self.regexes["html_tag"].sub(str(), str(title_tag))
		# Authors
		authors_tag = soup.find('p', class_="lead")
		authors = [self.regexes["html_tag"].sub(str(), str(a_tag)) for a_tag in authors_tag.find_all('a')]
		# Abstract
		abstract_tag = soup.find("div", class_="card-body acl-abstract")
		abstract = None
		if abstract_tag is None:
			logging.warning(f"Paper {paper_id} has no abstract!")
		else:
			abstract = self.regexes["html_tag"].sub(str(), str(abstract_tag))
			abstract = abstract.lstrip("Abstract")
		# Citation
		cite_acl_tag = soup.find("span", id="citeACL")
		cite_acl = self.regexes["html_tag"].sub(str(), str(cite_acl_tag))

		cite_informal_tag = soup.find("span", id="citeRichText")
		cite_informal = self.regexes["html_tag"].sub(str(), str(cite_informal_tag))
		# Bibtex
		if download_bibtex:
			url_bibtex = url_paper_detail + ".bib"
			response = self.easy_requests(method = "GET",
										  url = url_bibtex,
										  max_trial = -1,
										  headers = headers_paper_detail,
										  timeout = 30,
										  )
			with open(os.path.join(save_dir, f"{paper_id}.bib"), "wb") as f:
				f.write(response.content)
		# PDF
		if download_pdf:
			url_pdf = url_paper_detail + ".pdf"
			response = self.easy_requests(method = "GET",
										  url = url_pdf,
										  max_trial = -1,
										  headers = headers_paper_detail,
										  timeout = 30,
										  )
			with open(os.path.join(save_dir, f"{paper_id}.pdf"), "wb") as f:
				f.write(response.content)
		# Detail
		detail_dict = {
			"title": title,
			"authors": authors,
			"abstract": abstract,
			"cite_acl": cite_acl,
			"cite_informal": cite_informal,
		}
		with open(os.path.join(save_dir, f"{paper_id}.json"), 'w', encoding="utf8") as f:
			json.dump(detail_dict, f, indent=4)
		return detail_dict