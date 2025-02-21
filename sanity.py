# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import requests

url = "https://www.bqg128.com/user/geturl.html?url=https://www.bqg128.com/book/51676/1.html"

headers = """accept: text/html
accept-encoding: gzip, deflate
accept-language: zh-CN,zh;q=0.9
cookie: Hm_lvt_a4f729f0d035db225bffb944d51901aa=1737262848; HMACCOUNT=A940353C78CE7888; getsite=bq02.cc; hm=8a704070b913bd0cc6f2e7339cefa85f; hmt=1737262933; goad=1; Hm_lpvt_a4f729f0d035db225bffb944d51901aa=1737264407
priority: u=0, i
referer: https://www.bqg128.com/book/51676/
sec-ch-ua: "Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-origin
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"""

def headers_to_dict(headers: str) -> dict:
	lines = headers.splitlines()
	headers_dict = {}
	for line in lines:
		key, value = line.strip().split(':', 1)
		headers_dict[key.strip()] = value.strip()
	return headers_dict

r = requests.get(url, headers=headers_to_dict(headers))
print(r)
print(r.text)