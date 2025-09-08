# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import re
import time
import json
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urljoin
from datetime import datetime, timedelta

from src.crawlers.base import BaseCrawler
from src.crawlers.kuwo import CRAWLER_NAME

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class KuwoCrawler(BaseCrawler):
	url_host = "https://www.kuwo.cn/"
	url_summary = {
		"play_detail": urljoin(url_host, "/play_detail/{}"),
		"playurl": urljoin(url_host, "/api/v1/www/music/playUrl?"),
	}
	headers = {
		"chrome": """Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Cookie: _ga=GA1.2.1337706080.1750340238; Hm_lvt_cdb524f42f0ce19b169a8071123a4797=1757344493; HMACCOUNT=696F811D40074805; _gid=GA1.2.990418215.1757344493; _gat=1; Hm_lpvt_cdb524f42f0ce19b169a8071123a4797=1757344646; _ga_ETPBRPM9ML=GS2.2.s1757344493$o2$g1$t1757344646$j60$l0$h0; Hm_Iuvt_cdb524f42f23cer9b268564v7y735ewrq2324=5jcHtrBxc85YpNyH46E5jsS8s4Y2R7t6
Host: www.kuwo.cn
Pragma: no-cache
Referer: https://www.kuwo.cn/play_detail/32673026
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
Secret: 163ae8ea65552a53bd1d95c83bf4c8653cf9b4e25d89cf3f7ab422abd4b111ba0278d437
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
sec-ch-ua: "Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: \"Windows\"""",
	}

	def __init__(self, **kwargs):
		super(KuwoCrawler, self).__init__(**kwargs)
		self.regexes["html_tag"] = re.compile(r"<[^>]+>|\t")	# Remove HTML tags, including '\t' only
		self.download_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "download")	# Save the downloaded data
		os.makedirs(self.download_dir, exist_ok=True)

	# @param mid: Str, e.g. 32673026
	# @param save_path: Str, mp3 file saving path
	def easy_download(self, mid, save_path = None):
		query_string_dict = {
			"mid": mid,
			"type": "music",
			"httpsStatus": 1,
			"reqId": "f485ad61-8cc6-11f0-a416-8b54f5e288e8",
			"plat": "web_www",
			"from": str(),
		}
		query_string = urlencode(query_string_dict)
		query_url = self.url_summary["playurl"] + query_string
		response = self.easy_requests(
			method = "GET",
			url = query_url,
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["chrome"]),
			timeout = 30,
		)
		json_response = json.loads(response.text)
		play_url = json_response["data"]["url"]
		r = requests.get(play_url)									
		if save_path is None: 
			save_path = f"Kuwo_{mid}"		
		with open(save_path, "wb") as f: 
			f.write(r.content)		
