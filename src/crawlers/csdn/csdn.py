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
from copy import deepcopy
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urljoin
from datetime import datetime, timedelta

from src.crawlers.base import BaseCrawler
from src.crawlers.csdn import CRAWLER_NAME

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class CSDNCrawler(BaseCrawler):
	url_host = "https://blog.csdn.net"
	url_formatter_user_by_domain = "https://{domain}.blog.csdn.net".format
	url_formatter_user_by_username = urljoin(url_host, "{username}").format
	api_article = "/article/details/"
	api_business_list = "/community/home-api/v1/get-business-list?"
	query_dict_of_api_business_list = {"page": 0,
									   "size": 100,
									   "businessType": "blog",
									   "orderby": str(),
									   "noMore": "false",
									   "year": str(),
									   "month": str(),
									   "username": "CY19980216",
									   }
	headers = {
		"business_list": """Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: max-age=0
Connection: keep-alive
Cookie: UN=CY19980216; p_uid=U010000; uuid_tt_dd=10_21307064330-1715775993889-823680; loginbox_strategy=%7B%22taskId%22%3A317%2C%22abCheckTime%22%3A1716248850138%2C%22version%22%3A%22ExpA%22%2C%22nickName%22%3A%22%E5%9B%9A%E7%94%9FCY%22%7D; UserName=CY19980216; UserInfo=3924197e7eb74e1cacd50487e3734f50; UserToken=3924197e7eb74e1cacd50487e3734f50; UserNick=%E5%9B%9A%E7%94%9FCY; AU=1E6; BT=1716251305656; Hm_up_6bcd52f51e9b3dce32bec4a3997715ac=%7B%22islogin%22%3A%7B%22value%22%3A%221%22%2C%22scope%22%3A1%7D%2C%22isonline%22%3A%7B%22value%22%3A%221%22%2C%22scope%22%3A1%7D%2C%22isvip%22%3A%7B%22value%22%3A%220%22%2C%22scope%22%3A1%7D%2C%22uid_%22%3A%7B%22value%22%3A%22CY19980216%22%2C%22scope%22%3A1%7D%7D; cf_clearance=JjjZkvsgtwPoAbZXAoENHf5nTq2sQ60Kn8ENYzhb_F4-1716795122-1.0.1.1-NVfPpMmRk51YKn4nV5l.Zm0iKQVbS4.rLa8fYEJ6jVyz31sDq.iLHT82nAsd7Dbm50SatYmxHqZ5vncTiwXvTA; CY19980216comment_new=1717312944809; creative_btn_mp=3; firstDie=1; c_segment=0; Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac=1717421941,1717423608,1717432166,1717464263; dc_sid=4e0892c76edcfac3cb10eb288276cfec; _clck=luwxxh%7C2%7Cfmc%7C0%7C1584; Hm_lvt_ec8a58cd84a81850bcbd95ef89524721=1716252732,1716898219,1717310231,1717467138; __gads=ID=10d615e0d8176c86:T=1714733034:RT=1717468533:S=ALNI_MZmPh08ek_gSlbRSFxldtQbg1UYEg; __gpi=UID=00000e07e7fceb5f:T=1714733034:RT=1717468533:S=ALNI_MYOVDrPKe1VnXmSifoXPC7YyR77sQ; __eoi=ID=8c740bc94506fe42:T=1714733034:RT=1717468533:S=AA-AfjaPgGThzURrrc23MEqebt5C; Hm_lpvt_ec8a58cd84a81850bcbd95ef89524721=1717468577; fpv=6933bd4b316c43a146bd9c14c19411ec; yd_captcha_token=ycvu5ENHqS88Tq29mVViJ/2ZWf8HkLGPPQMUl3YxTjW2jVRUaESPnlzXlnC/YnMJGIG/dATd+nvieED87JNobA%3D%3D; log_Id_click=553; dc_session_id=10_1717482208372.933443; c_pref=default; c_ref=default; c_first_ref=default; c_first_page=https%3A//blog.csdn.net/CY19980216%3Ftype%3Dblog; creativeSetApiNew=%7B%22toolbarImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20230921102607.png%22%2C%22publishSuccessImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20240229024608.png%22%2C%22articleNum%22%3A137%2C%22type%22%3A2%2C%22oldUser%22%3Atrue%2C%22useSeven%22%3Afalse%2C%22oldFullVersion%22%3Atrue%2C%22userName%22%3A%22CY19980216%22%7D; waf_captcha_marker=c1e07ffee09eb430386e27121c1d48f4fcc47834ac232643363201f34fabe46a; c_dsid=11_1717482456230.483734; c_page_id=default; log_Id_pv=1282; Hm_lpvt_6bcd52f51e9b3dce32bec4a3997715ac=1717482457; log_Id_view=31458; _clsk=dt7hxf%7C1717482457056%7C4%7C0%7Cs.clarity.ms%2Fcollect; dc_tos=sejlyc
Host: blog.csdn.net
Referer: https://blog.csdn.net/community/home-api/v1/get-business-list?page=0&size=100&businessType=blog&orderby=&noMore=false&year=&month=&username=CY19980216
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36
sec-ch-ua: "Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: \"Windows\"""",
		"article": """Host: caoyang.blog.csdn.net
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv: 95.0) Gecko/20100101 Firefox/95.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Cookie: loginbox_strategy=%7B%22taskId%22%3A349%2C%22abCheckTime%22%3A1714733033723%2C%22version%22%3A%22exp11%22%7D; UserName=CY19980216; UserInfo=3ce781b43eb6420ea8cdf3368afded2b; UserToken=3ce781b43eb6420ea8cdf3368afded2b; UserNick=%E5%9B%9A%E7%94%9FCY; AU=1E6; UN=CY19980216; BT=1714733111189; p_uid=U010000; Hm_up_6bcd52f51e9b3dce32bec4a3997715ac=%7B%22islogin%22%3A%7B%22value%22%3A%221%22%2C%22scope%22%3A1%7D%2C%22isonline%22%3A%7B%22value%22%3A%221%22%2C%22scope%22%3A1%7D%2C%22isvip%22%3A%7B%22value%22%3A%220%22%2C%22scope%22%3A1%7D%2C%22uid_%22%3A%7B%22value%22%3A%22CY19980216%22%2C%22scope%22%3A1%7D%7D; management_ques=1714734337812; CY19980216comment_new=1715137223907; Hm_lvt_ec8a58cd84a81850bcbd95ef89524721=1715684293; __gads=ID=10d615e0d8176c86:T=1714733034:RT=1715692121:S=ALNI_MZmPh08ek_gSlbRSFxldtQbg1UYEg; __gpi=UID=00000e07e7fceb5f:T=1714733034:RT=1715692121:S=ALNI_MYOVDrPKe1VnXmSifoXPC7YyR77sQ; __eoi=ID=8c740bc94506fe42:T=1714733034:RT=1715692121:S=AA-AfjaPgGThzURrrc23MEqebt5C; uuid_tt_dd=10_21307064330-1715775993889-823680; firstDie=1; _clck=luwxxh%7C2%7Cflx%7C0%7C1584; _clsk=qg2md%7C1716166249071%7C1%7C0%7Cn.clarity.ms%2Fcollect; dc_session_id=10_1716208509370.482603; c_first_ref=default; c_first_page=https%3A//caoyang.blog.csdn.net/; c_segment=0; Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac=1716080382,1716103706,1716166248,1716208510; creative_btn_mp=3; dc_sid=e7f0a018966b3f5993b7ba2df0c51410; log_Id_click=277; c_pref=default; c_ref=default; cf_clearance=cNdOudp_ToZnPsOzVXETodLoRfTpKjm5XsCAoVqKzdI-1716211289-1.0.1.1-24fARSoWbfhcecH9UNujVRFUiRbGIMpH7RssUmaF4642oOyyG24EkT3C9NPq0ss7c3l2Z6D0V2ZvfhcBGN.DSA; dc_tos=sdsd3w; __cf_bm=V9u3xoE5d96ONr2N4pIvKorqrYR6quz4OdOChBgWKNc-1716212318-1.0.1.1-ypqingbEAWBbtM3OF8TFBcqWVf2eISOggnKM5CtdoLMAWOgPMCH5pdFdSOlTBVvdEae2cXQW2MqXbon0uUEOwg; c_dsid=11_1716212317422.623130; c_page_id=default; log_Id_pv=653; Hm_lpvt_6bcd52f51e9b3dce32bec4a3997715ac=1716212318; creativeSetApiNew=%7B%22toolbarImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20230921102607.png%22%2C%22publishSuccessImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20240229024608.png%22%2C%22articleNum%22%3A137%2C%22type%22%3A2%2C%22oldUser%22%3Atrue%2C%22useSeven%22%3Afalse%2C%22oldFullVersion%22%3Atrue%2C%22userName%22%3A%22CY19980216%22%7D; log_Id_view=16584; dc_tos=sdsdyj
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Cache-Control: max-age=0""",
		"profile": """Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: max-age=0
Connection: keep-alive
Cookie: loginbox_strategy=%7B%22taskId%22%3A349%2C%22abCheckTime%22%3A1722437666285%2C%22version%22%3A%22exp11%22%7D; UserName=CY19980216; UserInfo=2ff2f9ee1de94b48955572d31323ad8d; UserToken=2ff2f9ee1de94b48955572d31323ad8d; UserNick=%E5%9B%9A%E7%94%9FCY; AU=1E6; UN=CY19980216; BT=1722437725771; p_uid=U010000; CY19980216comment_new=1720976876371; uuid_tt_dd=10_21307064330-1722440159564-699699; Hm_lvt_ec8a58cd84a81850bcbd95ef89524721=1722443761,1722502976; __gads=ID=de8ca29501ba7e0f:T=1722502980:RT=1722518734:S=ALNI_Mby4VKYROq8mfOhgKTuUoNmO7oQCA; __gpi=UID=00000eb0dad0d4ff:T=1722502980:RT=1722518734:S=ALNI_MZxCanyEgLWlIfM43bTaE3tQAF2Eg; __eoi=ID=10cce66ffde01668:T=1722502980:RT=1722518734:S=AA-AfjZ6KmnTd-j2a6PkDN8cucRJ; log_Id_click=63; c_pref=default; c_ref=default; c_first_ref=default; c_first_page=https%3A//caoyang.blog.csdn.net/; c_segment=3; firstDie=1; Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac=1722470416,1722528465,1722603315,1722619246; HMACCOUNT=4F7F24540F8E3DCD; _clck=1m989hh%7C2%7Cfnz%7C0%7C1673; dc_sid=6dee5ae4eeb22b1354933afd5fe51cb1; dc_session_id=10_1722639453805.551717; c_dsid=11_1722639453966.828547; c_page_id=default; log_Id_pv=162; Hm_lpvt_6bcd52f51e9b3dce32bec4a3997715ac=1722639455; creativeSetApiNew=%7B%22toolbarImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20230921102607.png%22%2C%22publishSuccessImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20240229024608.png%22%2C%22articleNum%22%3A139%2C%22type%22%3A2%2C%22oldUser%22%3Atrue%2C%22useSeven%22%3Afalse%2C%22oldFullVersion%22%3Atrue%2C%22userName%22%3A%22CY19980216%22%7D; creative_btn_mp=3; _clsk=1as6wk0%7C1722639455671%7C1%7C0%7Cx.clarity.ms%2Fcollect; log_Id_view=4013; dc_tos=shm5an
Host: caoyang.blog.csdn.net
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36
sec-ch-ua: "Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: \"Windows\"""",
	}
	watch_article_ids = []	# Default `watch_article_ids`
	read_article_ids = [
		"151874936", "152050815", "151968907", "148641567", "150592993",
		"148512070", "148512070", "148659260", "148677582", "148343981",
		"147596961", "147596875", "147936000", "147654635", "148382586",
		"147903242", "147568082", "147513573", "147464165", "147428712",
		"147162527", "147078723", "146883693", "143653279", "143471542",
		"144775662", "143628401", "145690187", "144010237", "145502672",
		"146468206", "146460808", "145088488", "146387569", "143099065",  
		"144596444", "144651727", "144133212", "144278328", "143869819",  
		"140899018", "142684656", "141498497", "140747915", "140621717",  
		"143350101", "143310248", "142441347", "135325071", "141369623",  
		"140595950", "139551143", "138088546", "137213986", "136645892",  
		"136088465", "135319365", "134483304", "134442145", "133832711",
	]	# Default `read_article_ids`

	def __init__(self,
				 **kwargs,
				 ):
		super(CSDNCrawler, self).__init__(**kwargs)
		self.monitor_save_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "monitor")	# Save the monitor data
		os.makedirs(self.monitor_save_dir, exist_ok=True)

	# Monitor and increase the view-count of articles
	# @param domain: High level CSDN users usually have DIY domain name, e.g. my domain name is "caoyang" and corresponding home page is "https://caoyang.blog.csdn.net"
	# @param username: CSDN username, e.g. my username is "CY19980216" and the corresponding home page is "https://blog.csdn.net/CY19980216"
	# @param watch_article_ids: Articles which are required to be watched to monitor the view-count, default `self.watch_article_ids`
	# @param read_article_ids: Articles which are required to be read to increase the view-count, default `self.read_article_ids`
	# @param max_view_count: Max view-count of `read_article_ids`
	# @param monitor_interval: Interval time between two loops
	# @param kwargs: Other keyword arguments used to update `self.query_dict_of_api_business_list`
	def monitor_user_data(self,
						  domain = "caoyang",
						  username = "CY19980216",
						  watch_article_ids = None,
						  read_article_ids = None,
						  max_view_count = 10000,
						  monitor_interval = 120,
						  **kwargs,
						  ):
		def _tag_to_number(_tag):
			_tag_string = str(_tag.string).replace(',', str())
			if _tag_string.isdecimal():
				return int(_tag_string)
			else:
				return -1
		running_timestamp = time.strftime("%Y%m%d%H%M%S")
		if watch_article_ids is None:
			watch_article_ids = self.watch_article_ids[:]
		if read_article_ids is None:
			read_article_ids = self.read_article_ids[:]
		if domain is None:
			url_user = self.url_formatter_user_by_username(username=username)
		else:
			url_user = self.url_formatter_user_by_domain(domain=domain)
		logging.info(f"`url_user: {url_user}")
		url_formatter_article = urljoin(url_user, self.api_article + "{article_id}").format
		query_dict = deepcopy(self.query_dict_of_api_business_list)
		query_dict["username"] = username
		for key, word in kwargs.items():
			if key in query_dict:
				query_dict[key] = word
		query_string = urlencode(query_dict)
		logging.info(f"Query string: {query_string}")
		url_business_list = urljoin(url_user, self.api_business_list + query_string)
		logging.info(f"`url_business_list`: {url_business_list}")
		headers_business_list = BaseCrawler.headers_to_dict(headers=self.headers["business_list"])
		headers_article = BaseCrawler.headers_to_dict(headers=self.headers["article"])
		headers_profile = BaseCrawler.headers_to_dict(headers=self.headers["profile"])
		while True:
			monitor_start_time = time.time()
			# ---------------------------------------------------------
			# Step 1: Read each article to increase read-count
			# ---------------------------------------------------------
			if read_article_ids:	
				for i, read_article_id in enumerate(read_article_ids):
					logging.info(f"Reading article {read_article_id} ...")
					response = self.easy_requests(
						method = "GET",
						url = url_formatter_article(article_id = read_article_id),
						max_trial = 5,
						headers = headers_article,
						timeout = 30,
					)
					if response is None:
						logging.warning(f"  - Fail to read article {read_article_id}!")
					else:
						logging.info(f"  - Successfully read article {read_article_id}!")	
						soup = BeautifulSoup(response.text, "lxml")
						read_count_span = soup.find("span", class_="read-count")
						read_count_string = str(read_count_span.string)
						read_count = int(self.regexes["number"].findall(read_count_string)[0])
						logging.info(f"  - Read count: {read_count_string}")
			# ---------------------------------------------------------
			# Step 2: Watch the statistics number of each article
			# ---------------------------------------------------------
			if watch_article_ids:
				while True:
					# Request for `business_list`
					response = self.easy_requests(
						method = "GET",
						url = url_business_list,
						max_trial = -1,
						headers = headers_business_list,
						timeout = 30,
					)
					json_response = response.json()
					try:
						# 2024/08/03 01:44:57
						# Structure of `json_response["data"]`:
						# - list: List[Dict],
						#   - Example: {"articleId":140595950,"title":"【更新】cyのMemo（20240722~）","description":"我TM自己镇楼","url":"https://caoyang.blog.csdn.net/article/details/140595950","type":1,"top":false,"forcePlan":false,"viewCount":699,"commentCount":0,"editUrl":"https://editor.csdn.net/md?articleId=140595950","postTime":"2024-07-22 23:10:48","diggCount":17,"formatTime":"2024.07.22","picList":["https://i-blog.csdnimg.cn/direct/45504ff585a942c6b21afc42b6c6f34a.jpeg"],"collectCount":16}
						#   - articleId: int, title: str, description: str
						#   - url: str, type: int, top: bool, viewCount: int
						#   - commentCount: int, editUrl: str, postTime: str
						#   - diggCount: int, formatTime: str
						#   - picList: list[str], collectCount: int
						# - total: Int, the number of articles published by this user
						business_list = json_response["data"]["list"]
						if business_list is None:
							logging.warning("Business list is None!")
							logging.info(f"Waiting for {self.reset_interval} seconds ...")
							time.sleep(self.reset_interval)
						else:
							logging.info("Successfully get business list!")
							break
					except Exception as exception:
						logging.warning(f"Error in processing business list: {exception}")
						logging.info(f"Wait for {self.reset_interval} seconds ...")
						time.sleep(self.reset_interval)
				business_dict = dict()	# Index `business_list` by `article_id`
				for data in business_list:
					article_id = str(data["articleId"])
					title = data["title"]
					description = data["description"]
					view_count = data["viewCount"]
					comment_count = data["commentCount"]
					digg_count = data["diggCount"]
					collect_count = data["collectCount"]
					business_dict[article_id] = {"title": title,
												 "description": description,
												 "view_count": view_count,
												 "comment_count": comment_count,
												 "digg_count": digg_count,
												 "collect_count": collect_count,
												 }
				# Check the statistics of each `watch_article_id`
				datetime_string = time.strftime("%Y-%m-%d %H:%M:%S")
				for watch_article_id in watch_article_ids:
					if watch_article_id in business_dict:
						logging.info(f"{watch_article_id} can be watched!")
						keys = list(business_dict[watch_article_id].keys())
						values = list(business_dict[watch_article_id].values())
						save_path = os.path.join(self.monitor_save_dir, f"{watch_article_id}.txt")
						if not os.path.exists(save_path):
							# Create file and write table headers
							with open(save_path, 'w', encoding="utf8") as f:
								f.write('\t'.join(keys) + "\tdatetime\n")
						with open(save_path, 'a', encoding="utf8") as f:
							f.write('\t'.join(map(str, values)) + f"\t{datetime_string}\n")
					else:
						logging.info(f"{watch_article_id} cannot be watched!")				
				# ---------------------------------------------------------
				# Step 3: Watch the statistics number of user profile
				# ---------------------------------------------------------
				statistics_numbers = list()
				while True:
					response = self.easy_requests(
						method = "GET",
						url = url_user,
						max_trial = -1,
						headers = headers_profile,
						timeout = 30,
					)
					html = response.text
					soup = BeautifulSoup(html, "lxml")
					user_profile_div = soup.find("div", class_="user-profile-head-info-r-c")	# Statistics number area 1
					achievement_box_ul = soup.find("ul", class_="aside-common-box-achievement")	# Statistics number area 1
					if user_profile_div is None:
						logging.warning("User profile is None!")
						logging.info(f"Waiting for {self.reset_interval} seconds ...")
						time.sleep(self.reset_interval)
					elif achievement_box_ul is None:
						logging.warning("Achievement box is None!")
						logging.info(f"Waiting for {self.reset_interval} seconds ...")
						time.sleep(self.reset_interval)
					else:						
						logging.info("Successfully find user profile and achievement box!")
						
						break
				statistics_number_divs = user_profile_div.find_all("div", class_="user-profile-statistics-num")
				achievement_number_spans = achievement_box_ul.find_all("span")
				statistics_numbers += map(_tag_to_number, statistics_number_divs)
				statistics_numbers += map(_tag_to_number, achievement_number_spans)
				datetime_string = time.strftime("%Y-%m-%d %H:%M:%S")
				save_path = os.path.join(self.monitor_save_dir, f"{username}.txt")
				if not os.path.exists(save_path):
					with open(save_path, 'w', encoding="utf8") as f:
						f.write("statistics\tdatetime\n")
				with open(save_path, 'a', encoding="utf8") as f:
					f.write(','.join(map(str, statistics_numbers)) + f"\t{datetime_string}\n")
				# ---------------------------------------------------------
				# Step 4: Interval
				# ---------------------------------------------------------
				monitor_end_time = time.time()
				consumed_interval = monitor_end_time - monitor_start_time
				if consumed_interval < monitor_interval:
					remain_interval = monitor_interval - consumed_interval
					logging.info(f"Remain interval for {remain_interval} seconds ...")
					time.sleep(remain_interval)

	# Display the monitor data of articles
	# @param watch_article_ids: List of articleId which are required to be displayed, default `self.watch_article_ids`
	# @param columns: List of columns which are required to be displayed, e.g. "title", "description", "view_count", "comment_count", "digg_count", "collect_count"
	# @param n_days_before: The number of days before to be displayed
	def display_watch_article_data(self,
								   watch_article_ids = None,
								   columns = ["view_count"],
								   n_days_before = 3,
								   ):
		if watch_article_ids is None:
			watch_article_ids = self.watch_article_ids[:]
		datetime_now = datetime.now()
		datetime_n_days_before = datetime.now() - timedelta(days=n_days_before)
		dataframe_slices = {column: list() for column in columns}
		# Display by different article and datetime
		for watch_article_id in watch_article_ids:
			file_path = os.path.join(self.monitor_save_dir, f"{watch_article_id}.txt")
			dataframe = pandas.read_csv(file_path, sep='\t', header=0)
			dataframe["datetime"] = pandas.to_datetime(dataframe["datetime"], format="%Y-%m-%d %H:%M:%S")
			dataframe = dataframe[dataframe["datetime"] >= datetime_n_days_before]
			latest_title = dataframe.loc[dataframe.shape[0] - 1, "title"]
			logging.info(f"Display article {watch_article_id}: {latest_title}")
			for column in columns:
				dataframe_slice = dataframe[[column, "datetime", "title"]].drop_duplicates(subset=column, keep="first").reset_index(drop=True)
				dataframe_slices[column].append(dataframe_slice)
				if dataframe_slice.shape[0] > 1:
					for i in range(1, dataframe_slice.shape[0]):
						count = dataframe_slice.loc[i, column]
						datetime_string = dataframe_slice.loc[i, "datetime"]
						logging.info(f"    - {count} {datetime_string}")
				else:
					logging.info(f"    - Current `{column}` is {dataframe_slice.loc[0, column]}, no evidence inspected since {dataframe_slice.loc[0, 'datetime']}!")
				logging.info('-' * 16)
		logging.info('#' * 16)
		# Display by datetime only
		for column in columns:
			combined_dataframe_slices = pandas.concat(dataframe_slices[column], axis=0).sort_values(by="datetime", ascending=True).reset_index(drop=True)
			for i in range(combined_dataframe_slices.shape[0]):
				title = combined_dataframe_slices.loc[i, "title"]
				count = combined_dataframe_slices.loc[i, column]
				datetime_string = combined_dataframe_slices.loc[i, "datetime"]
				logging.info(f"    - {title} {count} {datetime_string}")
