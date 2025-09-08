# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import re
import json
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
	url_summary = {
		"video_page": urljoin(url_host, "/video/{bvid}").format,
		"episode_page": urljoin(url_host, "/bangumi/play/{ep_id}").format,
		"video_pagelist": urljoin(url_api, "/x/player/pagelist?bvid={bvid}&jsonp=jsonp").format,
		"video_playurl": urljoin(url_api, "/x/player/playurl?cid={cid}&bvid={bvid}&qn=64&type=&otype=json").format,
		"episode_playurl": urljoin(url_api, "/pgc/player/web/playurl?ep_id={ep_id}&jsonp=jsonp").format,	
	}
	chunk_size = 1024
	cookies = """buvid3=679FD60F-3568-EFB7-A37A-6471A719397142096infoc; b_nut=1734990842; b_lsid=AA71DCFC_193F5834CFE; _uuid=10F3AE94F-E745-6E7F-D10E1-3A6102B19D7BE43139infoc; CURRENT_FNVAL=4048; buvid4=3EBFCAB8-C4C2-DFE7-029C-85ED50DF58A143096-024122321-WbHe0fz6uHGjBc44KujX9A%3D%3D; buvid_fp=81c4cd30d2ae76951bd9bc4a97bf0697; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzUyNTAwNDIsImlhdCI6MTczNDk5MDc4MiwicGx0IjotMX0.Tuhlbbvhqa0g_ZG6AJXdzqkFXtNmv2FYP7WVbNLzFDU; bili_ticket_expires=1735249982; sid=f0dnvwgv; rpdid=|(k|kYYRm|Ym0J'u~JRmm|)RR"""
	headers = {
		"pagelist": """Host: api.bilibili.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate, zstd
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
Accept-Encoding: gzip, deflate, zstd
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Priority: u=0, i""",
		"download": """User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Origin: https://www.bilibili.com
Referer: https://www.bilibili.com""",	# Incomplete headers for downloading video stream (Lack `Host`, `Range` and `Cookie`)
		"page": f"""Host: www.bilibili.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate, zstd
Connection: keep-alive
Cookie: {cookies}
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Priority: u=0, i
TE: trailers""",	# Headers for visit video/episode webpages
		"common": """User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Accept: */*
Accept-Encoding: identity
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate, br
Cache-Control: no-cache
Origin: https://www.bilibili.com
Pragma: no-cache
Connection: keep-alive""",	# Common headers for requests
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
		self.regexes["playurl_ssr_data"] = re.compile(r"const playurlSSRData = (.*?)</script>")	# This contains data like playinfo
		self.regexes["playinfo"] = re.compile(r"<script>window.*?__playinfo__=(.*?)</script>")	# This is playinfo
		self.regexes["bvid"] = re.compile(r"\"bvid\":\"(.*?)\",")	# Simply find bvid on page source

	# Extract BVID in page source
	def _find_bvid_in_page_source(self, page_source):
		bvids = self.regexes["bvid"].findall(page_source, re.S)
		if not bvids:
			raise Exception("No initial states and BVID found in page source")
		return bvids[-1]

	# 2024/12/28 02:21:18
	# It is hard to use regex to match playurlSSRData!
	# We use loop to match nested structure like dictionary
	@classmethod
	def _find_playurl_ssr_data(cls, page_source):
		start_at = page_source.find("const playurlSSRData =")
		if start_at == -1:
			raise Exception("There is no playurlSSRData found in page source")
		matched_results = cls.easy_match_nest_structure(
			string = page_source,
			nest_symbol = ('{', '}'),
			start_at = start_at,
			max_return = 1,
		)
		playurl_ssr_data = json.loads(matched_results[0])
		return playurl_ssr_data

	# This playurl is for voiced video
	# @param durlinfo: Only for `source = "durl"`, JSON response from `playlist` URL or extracted by `playinfo["data"]["durl"][0]` regex on pages
	# @param videoinfo: Only for `source = "dash"`
	# @param audioinfo: Only for `source = "dash"`
	# @param source: Key in `playinfo["data"]`, e.g. "durl" or "dash"
	# - If source is "durl", then the returned `playurl` is directed to voiced video
	# - If source is "dash", then the returned `playurl` is split into `video_playurl` and `audio_playurl`
	# @param priority:
	# - If source is "durl", you can pass value like `["url", "backup_url"]`
	# - If source is "dash", you can pass value like `["backupUrl", "backup_url", "baseUrl", "base_url"]`
	@classmethod
	def _find_playurl_in_playinfo(cls,
								  durlinfo = None,
								  videoinfo = None,
								  audioinfo = None,
								  source = "durl",
								  priority = None,
								  ):
		if source == "durl":
			if priority is None:
				priority = ["url", "backup_url"]
			for key in priority:
				if key in durlinfo:
					logging.info(f"Find playurl in `{key}`!")
					return durlinfo[key]
			logging.warning(f"Nothing found by {priority}")
			return None
				
		elif source == "dash":
			if priority is None:
				priority = ["backupUrl", "backup_url", "baseUrl", "base_url"]
			def _easy_find_playurl(_playinfo):
				for _key in priority:
					if _key in _playinfo:
						logging.info(f"  - Find playurl in `{_key}`!")
						if isinstance(_playinfo[_key], str):
							return _playinfo[_key]
						elif isinstance(_playinfo[_key], list):
							return _playinfo[_key][-1]
						else:
							raise Exception(f"  - Unknown data type: {_playinfo[_key]}")
						break	
				logging.warning(f"  - No {source} found in playinfo:\n{_playinfo}")		
				return None
			logging.info("Find video playurl ...")
			video_playurl = _easy_find_playurl(videoinfo)
			logging.info("Find audio playurl ...")
			audio_playurl = _easy_find_playurl(audioinfo)
			return video_playurl, audio_playurl
		else:
			raise Exception(f"Unknown source: {source}")

	# Download by video and audio playurl
	def _download_video_and_audio(self,
								  bvid,
								  video_playurl,
								  audio_playurl,
								  video_save_path,
								  audio_save_path,
								  ):
		# First make a fake request to get `Content-Range` in response headers
		fake_headers = BaseCrawler.headers_to_dict(headers=self.headers["common"])
		fake_headers["Referer"] = self.url_summary["video_page"](bvid=bvid)
		fake_headers["Range"] = "bytes=0-299"	# Fake range
		video_response = requests.get(video_playurl, headers=fake_headers, stream=True)
		audio_response = requests.get(audio_playurl, headers=fake_headers, stream=True)
		video_size = int(video_response.headers["Content-Range"].split('/')[-1])
		audio_size = int(audio_response.headers["Content-Range"].split('/')[-1])
		video_total = video_size // self.chunk_size
		audio_total = audio_size // self.chunk_size // 2	# Audio need to be split into two parts
		# Next make a real request to download full video and audio
		real_headers = BaseCrawler.headers_to_dict(headers=self.headers["common"])
		real_headers["Referer"] = self.url_summary["video_page"](bvid=bvid)
		real_headers["Range"] = f"bytes=0-{video_size}"	# Real range
		self._download_stream(url = video_playurl, 
							  headers = real_headers, 
							  total = video_total,
							  save_path = video_save_path,
							  )
		# * Note: downloading full audio at one time is forbidden
		# * We have to download audio in two parts
		with open(audio_save_path, "wb") as f:			
			real_headers["Range"] = f"bytes={0}-{audio_size // 2}"
			response = requests.get(audio_playurl, headers=real_headers, stream=True)
			for byte in tqdm(response.iter_content(self.chunk_size), desc="Download audio part 1", total=audio_total):
				f.write(byte)
			real_headers["Range"] = f"bytes={audio_size // 2 + 1}-{audio_size}"
			response = requests.get(audio_playurl, headers=real_headers, stream=True)
			for byte in tqdm(response.iter_content(self.chunk_size), desc="Download audio part 2", total=audio_total):
				f.write(byte)

	# Use the playurl in `playinfo["data"]["durl"]` to download
	def _download_by_durl(self,
						  durlinfo,
						  save_path,
						  priority = ["url", "backup_url"],
						  ):
		size = durlinfo["size"]
		total = size // self.chunk_size
		playurl = BilibiliCrawler._find_playurl_in_playinfo(
			durlinfo = durlinfo,
			videoinfo = None,
			audioinfo = None,
			source = "durl",
			priority = priority,
		)
		assert playurl is not None, f"Cannot find playurl in `durl`:\n{durlinfo}"
		logging.info(f"Video size: {size}")
		# Download video
		download_headers = BaseCrawler.headers_to_dict(headers=self.headers["download"])
		# download_headers["Host"] = self.regexes["host"].findall(playurl)[0]
		download_headers["Range"] = f"bytes=0-{size}"
		# download_headers["Range"] = f"bytes={size + 1}-{size + size + 1}"
		# download_headers["Cookie"] = self.cookies
		self._download_stream(url = playurl, 
							  headers = download_headers, 
							  total = total,
							  save_path = save_path,
							  )
		logging.info(f"Save video at {save_path}")		

	# Use the videoinfo and audioinfo in `playinfo["data"]["dash"]` to download video
	def _download_video_by_dash(self,
								bvid,
								playinfo,
								video_save_path,
								audio_save_path,
								):
		videoinfo = playinfo["data"]["dash"]["video"][0]
		audioinfo = playinfo["data"]["dash"]["audio"][0]
		video_playurl, audio_playurl = BilibiliCrawler._find_playurl_in_playinfo(
			durlinfo = None,
			videoinfo = videoinfo,
			audioinfo = audioinfo,
			source = "dash",
			priority = ["backupUrl", "backup_url", "baseUrl", "base_url"],
		)
		self._download_video_and_audio(
			bvid = bvid,
			video_playurl = video_playurl,
			audio_playurl = audio_playurl,
			video_save_path = video_save_path,
			audio_save_path = audio_save_path,
		)

	# Use the videoinfo and audioinfo in `playinfo["data"]["dash"]` to download episode
	def _download_episode_by_dash(self,
								  bvid,
								  playurl_ssr_data,
								  video_save_path,
								  audio_save_path,
								  ):
		videoinfo = playurl_ssr_data["result"]["video_info"]["dash"]["video"][0]
		audioinfo = playurl_ssr_data["result"]["video_info"]["dash"]["audio"][0]
		video_playurl, audio_playurl = BilibiliCrawler._find_playurl_in_playinfo(
			durlinfo = None,
			videoinfo = videoinfo,
			audioinfo = audioinfo,
			source = "dash",
			priority = ["backupUrl", "backup_url", "baseUrl", "base_url"],
		)
		self._download_video_and_audio(
			bvid = bvid,
			video_playurl = video_playurl,
			audio_playurl = audio_playurl,
			video_save_path = video_save_path,
			audio_save_path = audio_save_path,
		)

	# Download stream
	def _download_stream(self, url, headers, total, save_path):
		response = requests.get(url, headers=headers, stream=True, verify=False)
		with open(save_path, "wb") as f:
			for byte in tqdm(response.iter_content(self.chunk_size), desc="Download process", total=total):
				f.write(byte)
				
	# Download video by bvid
	def easy_download_video(self, bvid, save_path = None):
		if save_path is None:
			save_path = os.path.join(self.download_dir, f"{bvid}.mp4")
		# 2024/12/24 05:26:28 `self.url_summary["video_pagelist"]` has been deprecated
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
			url = self.url_summary["video_pagelist"](bvid=bvid),
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
			url = self.url_summary["video_playurl"](cid=cid, bvid=bvid),
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["playurl"]),
			timeout = 30,
		).json()
		self._download_by_durl(
			durlinfo = playurl_json["data"]["durl"][0],
			save_path = save_path,
			priority = ["url", "backup_url"],
		)

	# Download episode by ep_id
	# 2024/12/28 03:50:47 This is now unavailable
	def easy_download_episode(self, ep_id, save_path=None):
		if save_path is None:
			save_path = os.path.join(self.download_dir, f"{ep_id}.mp4")
		# Request for playurl and size of episode
		playurl_json = self.easy_requests(
			method = "GET",
			url = self.url_summary["episode_playurl"](ep_id=ep_id),
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["playurl"]),
			timeout = 30,
		).json()
		self._download_by_durl(
			durlinfo = playurl_json["data"]["durl"][0],
			save_path = save_path,
			priority = ["backup_url", "url"],
		)

	# General method by parsing page source
	# In fact we only need bvid
	# Each episode of an anime also has a bvid and a corresponding bvid-URL which is redirected to another episode link
	# e.g. https://www.bilibili.com/video/BV1rK4y1b7TZ is redirected to https://www.bilibili.com/bangumi/play/ep322903
	def download(self, 
				 bvid,
				 save_path = None,
				 video_save_path = None, 
				 audio_save_path = None,
				 ):
		if save_path is None:
			save_path = os.path.join(self.download_dir, f"{bvid}.mp4")
		if video_save_path is None:
			video_save_path = os.path.join(self.download_dir, f"{bvid}.m4s")
		if audio_save_path is None:
			audio_save_path = os.path.join(self.download_dir, f"{bvid}.mp3")
		# Find playinfo
		page_html = self.easy_requests(
			method = "GET",
			url = self.url_summary["video_page"](bvid=bvid),
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["page"]),
			timeout = 30,
		).text
		playinfos = self.regexes["playinfo"].findall(page_html, re.S)
		if playinfos:
			playinfo = json.loads(playinfos[0])	
			# Find playurl
			if "durl" in playinfo["data"]:
				logging.info("Download by durl ...")
				self._download_by_durl(
					durlinfo = playinfo["data"]["durl"][0],
					save_path = save_path,
					priority = ["url", "backup_url"],
				)
			elif "dash" in playinfo["data"]:
				self._download_video_by_dash(
					bvid = bvid,
					playinfo = playinfo,
					video_save_path = video_save_path,
					audio_save_path = audio_save_path,
				)
			else:
				raise Exception(f"No data found in playinfo\n{playinfo}")

		else:
			logging.info(f"No playinfo found in bvid {bvid}, try playURLSSRData ...")
			# 2024/12/28 02:25:42If there is no `initial_states`, then we find playurlSSRData
			playurl_ssr_data = BilibiliCrawler._find_playurl_ssr_data(page_source = page_html)

			self._download_episode_by_dash(
				bvid = bvid,
				playurl_ssr_data = playurl_ssr_data,
				video_save_path = video_save_path,
				audio_save_path = audio_save_path,
			)
		
	# Download with page URL
	# e.g.
	# >>> url = "https://www.bilibili.com/video/BV1jf4y1h73r"
	# >>> url = "https://www.bilibili.com/bangumi/play/ep399420"
	# 2024/12/27 23:36:44 BVID can be found in page source:
	# >>> url = "https://www.bilibili.com/video/BV1jf4y1h73r" ==> `window.__INITIAL_STATE__`
	# >>> url = "https://www.bilibili.com/bangumi/play/ep399420" ==> `const playurlSSRData`, this is also `window.__playinfo__`
	def easy_download(self, url):
		page_html = self.easy_requests(
			method = "GET",
			url = url,
			max_trial = 5,
			headers = BaseCrawler.headers_to_dict(headers=self.headers["page"]),
			timeout = 30,
		).text
		initial_states = self.regexes["initial_state"].findall(page_html, re.S)
		if not initial_states:
			bvid = self._find_bvid_in_page_source(page_source = page_html)
			self.download(
				bvid = bvid,
				save_path = os.path.join(self.download_dir, f"{bvid}.mp4"),
				video_save_path = os.path.join(self.download_dir, f"{bvid}.m4s"),
				audio_save_path = os.path.join(self.download_dir, f"{bvid}.mp3"),
			)
			return 0
		initial_state = json.loads(initial_states[0])
		episode_list = initial_state.get("epList")
		if episode_list is not None:
			# Download anime with several episodes
			episode_name = self.regexes["episode_name"].findall(page_html, re.S)[0].strip()
			for episode in episode_list:
				episode_badge = episode["badge"]
				if episode_badge != "会员":	# No VIP required
					logging.info(f"Episode badge is {episode_badge}!")
					save_dir = os.path.join(self.download_dir, episode_name)
					os.makedirs(save_dir, exist_ok=True)
					video_title = episode["titleFormat"] + episode["longTitle"]
					video_title_valid = self.regexes["forbidden_filename_char"].sub(str(), video_title)
					self.download(
						bvid = str(episode["bvid"]),
						save_path = os.path.join(save_dir,  + f"{video_title_valid}.mp4"),
						video_save_path = os.path.join(save_dir, f"{video_title_valid}.m4s"),
						audio_save_path = os.path.join(save_dir, f"{video_title_valid}.mp3"),
					)
				else:	# Unable to download VIP anime
					logging.warning(f"Permission denied: badge is {episode_badge}")
			return 1
		else:
			# Download videos which are not episode
			bvid = initial_state["bvid"]
			video_data = initial_state["videoData"]
			video_title = video_data["title"]
			video_title_valid = self.regexes["forbidden_filename_char"].sub(str(), video_title)
			self.download(
				bvid = bvid,
				save_path = os.path.join(self.download_dir, f"{video_title_valid}.mp4"),
				video_save_path = os.path.join(self.download_dir, f"{video_title_valid}.m4s"),
				audio_save_path = os.path.join(self.download_dir, f"{video_title_valid}.mp3"),
			)
			return 2
