# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import re
import time
import math
import json
import base64
import codecs
import random
import logging
import requests
from Crypto.Cipher import AES
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urljoin
from datetime import datetime, timedelta

from src.crawlers.base import BaseCrawler
from src.crawlers.netease import CRAWLER_NAME

from settings import CRAWLER_DATA_DIR, TEMP_DIR

class NeteaseCrawler(BaseCrawler):
	url_host = "https://music.163.com/"
	url_summary = {
		"playurl": urljoin(url_host, "/weapi/song/enhance/player/url?csrf_token="),
	}
	headers = {
		"simple": """User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0""",
	}
	def __init__(self, **kwargs):		
		super(NeteaseCrawler, self).__init__(**kwargs)	
		self.download_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "download")	# Save the downloaded data
		os.makedirs(self.download_dir, exist_ok=True)

	
	def easy_download(self, song_id, save_path = None):
		formdata = self._encrypt_formdata(song_id)		
		response = self.easy_requests(
			method = "POST",
			url = self.url_summary["playurl"],
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["simple"]),
			timeout = 30,
			data = formdata,
		)					
		json_response = json.loads(response.text)
		play_url = json_response["data"][0]["url"]					
		response = self.easy_requests(
			method = "GET",
			url = play_url,
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["simple"]),
			timeout = 30,
		)								
		if save_path is None: 
			save_path = os.path.join(self.download_dir, f"Netease_{song_id}.mp3")					
		with open(save_path, "wb") as f: 
			f.write(response.content)	
	
	def _encrypt_formdata(self, song_id, driver = None):
		d = """{"ids":"[%s]","br":128000,"csrf_token":""}"""
		e = """010001"""					
		f = """00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"""
		g = """0CoJUm6Qyw8W8jud"""									
		d %= song_id													
		if driver is not None:
			# Encrypt formdata by executing Javascript using webdriver 											
			JS = """return window.asrsea("{}", "{}", "{}", "{}")""".format(d, e, f, g)
			driver.get(self.url_song.format(song_id))
			formdata = driver.execute_script(JS)						
			formdata = dict(params=formdata["encText"], encSecKey=formdata["encSecKey"])
			return formdata
			
		def _javascript2python_a(a):									
			b = """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"""
			c = str()
			for i in range(a): 
				c += b[math.floor(random.random() * len(b))]
			return c
 
		def _javascript2python_b(a, b):									
			pad = 16 - len(a.encode()) % 16								
			a += pad * chr(pad)											
			encryptor = AES.new(b.encode("utf8"), AES.MODE_CBC, b"0102030405060708")	
			f = base64.b64encode(encryptor.encrypt(a.encode("UTF-8")))
			return f
			
		def _javascript2python_c(a, b, c):								
			b = b[::-1]													
			e = int(codecs.encode(b.encode("utf8"), "hex_codec"), 16) ** int(a, 16) % int(c, 16)
			return format(e, 'x').zfill(256)							
 
		random_text = _javascript2python_a(16)							
		params = _javascript2python_b(d, g)								
		params = _javascript2python_b(params.decode("utf8"), random_text)
		encSecKey = _javascript2python_c(e, random_text, f)				
		formdata = dict(params=params, encSecKey=encSecKey)				
		return formdata	
