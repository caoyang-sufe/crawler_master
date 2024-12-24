# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import re
import time
import random
import pandas
import logging
import requests
from tqdm import tqdm
from copy import deepcopy
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urljoin
from datetime import datetime, timedelta

from src.crawlers.bilibili import CRAWLER_NAME
from src.crawlers.base import BaseCrawler

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class BilibiliCrawler(BaseCrawler):
	url_host = "https://www.bilibili.com"
	url_api = "https://api.bilibili.com"
	url_bilibili_summary = {
		"video_page": urljoin(url_host, "/video/{bvid}").format,
		"episode_page": urljoin(url_host, "/bangumi/play/{ep_id}").format,
		"video_pagelist": urljoin(url_api, "/x/player/pagelist?bvid={bvid}&jsonp=jsonp").format,
		"video_pageurl": urljoin(url_api, "/x/player/playurl?cid={cid}&bvid={bvid}&qn=64&type=&otype=json").format,
		"episode_playurl": urljoin(url_api, "/pgc/player/web/playurl?ep_id={ep_id}&jsonp=jsonp").format,	
	}
	chunk_size = 1024
	cookies = """buvid3=679FD60F-3568-EFB7-A37A-6471A719397142096infoc; b_nut=1734990842; b_lsid=AA71DCFC_193F5834CFE; _uuid=10F3AE94F-E745-6E7F-D10E1-3A6102B19D7BE43139infoc; CURRENT_FNVAL=4048; buvid4=3EBFCAB8-C4C2-DFE7-029C-85ED50DF58A143096-024122321-WbHe0fz6uHGjBc44KujX9A%3D%3D; buvid_fp=81c4cd30d2ae76951bd9bc4a97bf0697; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzUyNTAwNDIsImlhdCI6MTczNDk5MDc4MiwicGx0IjotMX0.Tuhlbbvhqa0g_ZG6AJXdzqkFXtNmv2FYP7WVbNLzFDU; bili_ticket_expires=1735249982; sid=f0dnvwgv; rpdid=|(k|kYYRm|Ym0J'u~JRmm|)RR"""
	headers = {
		"pagelist": """Host: api.bilibili.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Priority: u=0, i
TE: trailers""",
		"playurl": """Host: api.bilibili.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Priority: u=0, i""",
		"download": """User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Origin: https://www.bilibili.com
Referer: https://www.bilibili.com""",
		"page": f"""Host: www.bilibili.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
Cookie: {cookies}
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Priority: u=0, i
TE: trailers"""
	}
	def __init__(self,
				 **kwargs,
				 ):
		super(BilibiliCrawler, self).__init__(**kwargs)
		self.download_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "download")	# Save the downloaded data
		os.makedirs(self.download_dir, exist_ok=True)
		# Add regular expressions to BaseCrawler.regexes
		self.regexes["episode_name"] = re.compile(r"meta name=\"keywords\" content=\"(.*?)\"")
		self.regexes["initial_state"] = re.compile(r"<script>window.__INITIAL_STATE__=(.*?);")
		self.regexes["playinfo"] = re.compile(r"<script>window.*?__playinfo__=(.*?)</script>")

	# Download video by bvid
	def easy_download_video(self, bvid, save_path = None):
		if save_path is None:
			save_path = os.path.join(self.download_dir, f"{bvid}.mp4")
		# 2024/12/24 05:26:28 `self.url_bilibili_summary["video_pagelist"]` has been deprecated
		# 2024/12/24 05:26:32 The JSON Response appears like:
		# {
			# "code": 0,
			# "message": "0",
			# "ttl": 1,
			# "data": [{
					# "cid": 536484,
					# "page": 1,
					# "from": "vupload",
					# "part": "",
					# "duration": 282,
					# "vid": "",
					# "weblink": "",
					# "dimension": {
						# "width": 636,
						# "height": 360,
						# "rotate": 0
					# }
				# }
			# ]
		# }		
		pagelist_json = self.easy_requests(
			method = "GET",
			url = self.url_bilibili_summary["video_pagelist"](bvid=bvid),
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["pagelist"]),
			timeout = 30,
		).json()
		cid = pagelist_json["data"][0]["cid"]
		video_title = pagelist_json["data"][0]["part"]	# Maybe empty string in old videos
		logging.info(f"Video title: {video_title}")
		# Request for playurl and size of video
		playurl_json = self.easy_requests(
			method = "GET",
			url = self.url_bilibili_summary["video_playurl"](cid=cid, bvid=bvid),
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["playurl"]),
			timeout = 30,
		).json()
		try:
			video_playurl = playurl_json["data"]["durl"][0]["url"]
		except Exception as exception:
			logging.warning(f"Fail to get playurl: {exception}")
			video_playurl = playurl_json["data"]["durl"][0]["backup_url"][0]	
		video_size = playurl_json["data"]["durl"][0]["size"]
		total = video_size // self.chunk_size
		logging.info(f"Video size: {video_size}")
		# Download video
		download_headers = BaseCrawler.headers_to_dict(headers=self.headers["download"])
		download_headers["Host"] = self.regexes["host"].findall(video_playurl)[0]
		download_headers["Range"] = f"bytes=0-{video_size}"
		response = requests.get(video_playurl, headers=download_headers, stream=True, verify=False)
		with open(save_path, "wb") as f:
			for byte in tqdm(response.iter_content(self.chunk_size), desc="Download process", total=total):
				f.write(byte)

	# Download episode by ep_id
	def easy_download_episode(self, ep_id, save_path=None):
		if save_path is None:
			save_path = os.path.join(self.download_dir, f"{ep_id}.mp4")
		# Request for playurl and size of episode
		playurl_json = requests.get(self.url_bilibili_summary["episode_playurl"](ep_id=ep_id)).json
		try:
			episode_playurl = playurl_json["result"]["durl"][0]["backup_url"][0]
		except:
			logging.warning(f"Fail to get playurl: {exception}")
			episode_playurl = playurl_json["result"]["durl"][0]["url"]
		episode_size = playurl_json["result"]["durl"][0]["size"]
		total = episode_size // self.chunk_size
		logging.info(f"Episode size: {episode_size}")
		# Download episode
		download_headers = BaseCrawler.headers_to_dict(headers=self.headers["download"])
		download_headers = {
			"User-Agent": self.user_agent,
			"Origin"	: "https://www.bilibili.com",
			"Referer"	: "https://www.bilibili.com",	
			# "Cookie"	: 
		}
		download_headers["Host"] = re.findall(self.regexes["host"], episode_playurl, re.I)[0]
		download_headers["Range"] = f"bytes=0-{episode_size}"
		# download_headers["Cookie"] = """innersign=0; buvid3=3D8F234E-5DAF-B5BD-1A26-C7CDE57C21B155047infoc; i-wanna-go-back=-1; b_ut=7; b_lsid=1047C7449_1808035E0D6; _uuid=A4884E3F-BF68-310101-E5E6-10EBFDBCC10CA456283infoc; buvid_fp=82c49016c72d24614786e2a9e883f994; buvid4=247E3498-6553-51E8-EB96-C147A773B34357718-022050123-7//HOhRX5o4Xun7E1GZ2Vg%3D%3D; fingerprint=1b7ad7a26a4a90ff38c80c37007d4612; sid=jilve18q; buvid_fp_plain=undefined; SESSDATA=f1edfaf9%2C1666970475%2Cf281c%2A51; bili_jct=de9bcc8a41300ac37d770bca4de101a8; DedeUserID=130321232; DedeUserID__ckMd5=42d02c72aa29553d; nostalgia_conf=-1; CURRENT_BLACKGAP=1; CURRENT_FNVAL=4048; CURRENT_QUALITY=0; rpdid=|(u~||~uukl)0J"uYluRu)l|J"""
		response = requests.get(episode_playurl, headers=headers, stream=True, verify=False)
		with open(save_path, "wb") as f:
			for byte in tqdm(response.iter_content(self.chunk_size), desc="Download process", total=total):
				f.write(byte)

	# General method by parsing page source
	def download_video_and_audio(self, bvid, video_save_path=None, audio_save_path=None) -> dict:
		if video_save_path is None:
			video_save_path = os.path.join(self.download_dir, f"{bvid}.m4s")
		if audio_save_path is None:
			audio_save_path = os.path.join(self.download_dir, f"{bvid}.mp3")
		common_headers = {
			"Accept"			: "*/*",
			"Accept-encoding"	: "gzip, deflate, br",
			"Accept-language"	: "zh-CN,zh;q=0.9,en;q=0.8",
			"Cache-Control"		: "no-cache",
			"Origin"			: "https://www.bilibili.com",
			"Pragma"			: "no-cache",
			"Host"				: "www.bilibili.com",
			"User-Agent"		: self.user_agent,
		}

		# In fact we only need bvid
		# Each episode of an anime also has a bvid and a corresponding bvid-URL which is redirected to another episode link
		# e.g. https://www.bilibili.com/video/BV1rK4y1b7TZ is redirected to https://www.bilibili.com/bangumi/play/ep322903
		response = requests.get(self.video_webpage_link(bvid), headers=common_headers)
		html = response.text
		playinfos = re.findall(self.regexes["playinfo"], html, re.S)
		if not playinfos:
			raise Exception(f"No playinfo found in bvid {bvid}\nPerhaps VIP required")
		playinfo = json.loads(playinfos[0])
		
		# There exists four different URLs with observations as below
		# `baseUrl` is the same as `base_url` with string value
		# `backupUrl` is the same as `backup_url` with array value
		# Here hard code is employed to select playurl
		def _select_video_playurl(_videoinfo):
			if "backupUrl" in _videoinfo:
				return _videoinfo["backupUrl"][-1]
			if "backup_url" in _videoinfo:
				return _videoinfo["backup_url"][-1]
			if "baseUrl" in _videoinfo:
				return _videoinfo["baseUrl"]
			if "base_url" in _videoinfo:
				return _videoinfo["base_url"]	
			raise Exception(f"No video URL found\n{_videoinfo}")	
			
		def _select_audio_playurl(_audioinfo):
			if "backupUrl" in _audioinfo:
				return _audioinfo["backupUrl"][-1]
			if "backup_url" in _audioinfo:
				return _audioinfo["backup_url"][-1]
			if "baseUrl" in _audioinfo:
				return _audioinfo["baseUrl"]
			if "base_url" in _audioinfo:
				return _audioinfo["base_url"]
			raise Exception(f"No audio URL found\n{_audioinfo}")
		
		# with open(f"playinfo-{bvid}.js", "w") as f:
			# json.dump(playinfo, f)

		if "durl" in playinfo["data"]:
			video_playurl = playinfo["data"]["durl"][0]["url"]
			# video_playurl = playinfo["data"]["durl"][0]["backup_url"][1]
			print(video_playurl)
			video_size = playinfo["data"]["durl"][0]["size"]
			total = video_size // self.chunk_size
			print(f"Video size: {video_size}")
			headers = {
				"User-Agent": self.user_agent,
				"Origin"	: "https://www.bilibili.com",
				"Referer"	: "https://www.bilibili.com",			
			}
			headers["Host"] = re.findall(self.regexes["host"], video_playurl, re.I)[0]
			headers["Range"] = f"bytes=0-{video_size}"
			# headers["Range"] = f"bytes={video_size + 1}-{video_size + video_size + 1}"
			response = requests.get(video_playurl, headers=headers, stream=True, verify=False)
			tqdm_bar = tqdm(response.iter_content(self.chunk_size), desc="Download process", total=total)
			with open(video_save_path, "wb") as f:
				for byte in tqdm_bar:
					f.write(byte)
			return True

		elif "dash" in playinfo["data"]:
			videoinfo = playinfo["data"]["dash"]["video"][0]
			audioinfo = playinfo["data"]["dash"]["audio"][0]
			video_playurl = _select_video_playurl(videoinfo)
			audio_playurl = _select_audio_playurl(audioinfo)

		else:
			raise Exception(f"No data found in playinfo\n{playinfo}")

		# First make a fake request to get the `Content-Range` params in response headers
		fake_headers = {
			"Accept"			: "*/*",
			"Accept-Encoding"	: "identity",
			"Accept-Language"	: "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
			"Accept-Encoding"	: "gzip, deflate, br",
			"Cache-Control"		: "no-cache",
			"Origin"			: "https://www.bilibili.com",
			"Pragma"			: "no-cache",
			"Range"				: "bytes=0-299",
			"Referer"			: self.video_webpage_link(bvid),
			"User-Agent"		: self.user_agent,
			"Connection"		: "keep-alive",
		}
		response = requests.get(video_playurl, headers=fake_headers, stream=True)
		video_size = int(response.headers["Content-Range"].split("/")[-1])
		total = video_size // self.chunk_size
		
		# Next make a real request to download full video
		real_headers = {
			"Accept"			: "*/*",
			"accept-encoding"	: "identity",
			"Accept-Language"	: "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
			"Accept-Encoding"	: "gzip, deflate, br",
			"cache-control"		: "no-cache",
			"Origin"			: "https://www.bilibili.com",
			"pragma"			: "no-cache",
			"Range"				: f"bytes=0-{video_size}",
			"Referer"			: self.video_webpage_link(bvid),
			"User-Agent"		: self.user_agent,
			"Connection"		: "keep-alive",
		}
		response = requests.get(video_playurl, headers=real_headers, stream=True)
		tqdm_bar = tqdm(response.iter_content(self.chunk_size), desc="Download video", total=total)
		with open(video_save_path, "wb") as f:
			for byte in tqdm_bar:
				f.write(byte)
				
		# The same way for downloading audio
		response = requests.get(audio_playurl, headers=fake_headers, stream=True)
		audio_size = int(response.headers["Content-Range"].split("/")[-1])
		total = audio_size // self.chunk_size // 2
		
		# Confusingly downloading full audio at one time is forbidden
		# We have to download audio in two parts
		with open(audio_save_path, "wb") as f:
			audio_part = 0
			for (_from, _to) in [[0, audio_size // 2], [audio_size // 2 + 1, audio_size]]:
				headers = {
					"Accept": "*/*",
					"Accept-Encoding": "identity",
					"Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
					"Accept-Encoding": "gzip, deflate, br",
					"Cache-Control": "no-cache",
					"Origin": "https://www.bilibili.com",
					"Pragma": "no-cache",
					"Range": f"bytes={_from}-{_to}",
					"Referer": self.video_webpage_link(bvid),
					"User-Agent": self.user_agent,
					"Connection": "keep-alive",
				}
				audio_part += 1
				response = requests.get(audio_playurl, headers=headers, stream=True)
				tqdm_bar = tqdm(response.iter_content(self.chunk_size), desc=f"Download audio part{audio_part}", total=total)
				for byte in tqdm_bar:
					f.write(byte)
		return True


	# Download with page URL as below:
	# >>> url = "https://www.bilibili.com/video/BV1jf4y1h73r"
	# >>> url = "https://www.bilibili.com/bangumi/play/ep399420"
	def easy_download(self, url): 
		headers = {
			"Accept": "*/*",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
			"Cache-Control": "no-cache",
			"Origin": "https://www.bilibili.com",
			"Pragma": "no-cache",
			"Host": "www.bilibili.com",
			"User-Agent": self.user_agent,
		}		
		response = requests.get(url, headers=headers)
		html = response.text
		initial_states = re.findall(self.regexes["initial_state"], html, re.S)
		if not initial_states:
			raise Exception("No initial states found in page source")
		initial_state = json.loads(initial_states[0])
		
		# Download anime with several episodes
		episode_list = initial_state.get("epList")

		if episode_list is not None:
			name = re.findall(self.regexes["episode_name"], html, re.S)[0].strip()
			for episode in episode_list:
				if episode["badge"] != "会员":							 # No VIP required
					if not os.path.exists(name):
						os.mkdir(name)
					self.download(
						bvid=str(episode["bvid"]),
						video_save_path=os.path.join(name, episode["titleFormat"] + episode["longTitle"] + ".m4s"),
						audio_save_path=os.path.join(name, episode["titleFormat"] + episode["longTitle"] + ".mp3"),
					)
				else:													 # Unable to download VIP anime
					continue
		
		# Download common videos
		else:
			video_data = initial_state["videoData"]
			name = video_data["tname"].strip()
			if not os.path.exists(name):
				os.mkdir(name)
			self.download(
				bvid=str(episode["bvid"]),
				video_save_path=os.path.join(name, video_data["title"] + ".m4s"),
				audio_save_path=os.path.join(name, video_data["title"] + ".mp3"),
			)
		return True

