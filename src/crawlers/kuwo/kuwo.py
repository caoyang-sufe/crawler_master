# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import re
import time
import json
import random
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
Connection: keep-alive
Cookie: _ga=GA1.2.1813416839.1740056188; Hm_lvt_cdb524f42f0ce19b169a8071123a4797=1757564775; HMACCOUNT=56FF9AF0B986EDC9; _gid=GA1.2.1237564003.1757564775; Hm_lpvt_cdb524f42f0ce19b169a8071123a4797=1757564840; _ga_ETPBRPM9ML=GS2.2.s1757564775$o2$g1$t1757564839$j58$l0$h0; Hm_Iuvt_cdb524f42f23cer9b268564v7y735ewrq2324=kEJfnZhZFYawERasipCTSZBdXDMZWFBj
Host: www.kuwo.cn
Referer: https://www.kuwo.cn/play_detail/{}
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
Secret: 4815c1c47f7d0071987cc1e60ee8d05e61bfb28364a0de6351c436c3d1c027e6055ef1ec
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: \"Windows\"""",
	}

	def __init__(self, **kwargs):
		super(KuwoCrawler, self).__init__(**kwargs)
		self.download_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "download")	# Save the downloaded data
		os.makedirs(self.download_dir, exist_ok=True)

	# @param mid: Str, e.g. 32673026
	# @param save_path: Str, mp3 file saving path
	def easy_download(self, mid, save_path = None):
		query_string_dict = {
			"mid": mid,
			"type": "music",
			"httpsStatus": 1,
			"reqId": "5c0ffb40-8ec8-11f0-8efc-093e2a068f1d",
			"plat": "web_www",
			"from": '',
		}
		query_string = urlencode(query_string_dict)
		query_url = self.url_summary["playurl"] + query_string
		print(query_url)
		from pprint import pprint
		pprint(BaseCrawler.headers_to_dict(headers=self.headers["chrome"].format(mid)))
		response = self.easy_requests(
			method = "GET",
			url = query_url,
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["chrome"].format(mid)),
			timeout = 30,
		)
		json_response = json.loads(response.text)
		play_url = json_response["data"]["url"]
		response = self.easy_requests(
			method = "GET",
			url = play_url,
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["chrome"].format(mid)),
			timeout = 30,
		)								
		if save_path is None: 
			save_path = os.path.join(self.download_dir, f"Kuwo_{mid}.mp3")		
		with open(save_path, "wb") as f: 
			f.write(response.content)		
