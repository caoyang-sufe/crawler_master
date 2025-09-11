# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import sys
import time
import logging
import argparse

from src.crawlers import (
	ESGCrawler, 
	CSDNCrawler, 
	ACLAnthologyCrawler, 
	BilibiliCrawler, 
	QidianCrawler, 
	BQG128Crawler, 
	Bxwxx7Crawler, 
	Shu77Crawler,
	KuwoCrawler,
	NeteaseCrawler,
)
from src.tools.easy import initialize_logger, terminate_logger

from settings import CRAWLER_DATA_DIR, LOGGING_DIR, TEMP_DIR

def make_directories():
	os.makedirs(CRAWLER_DATA_DIR, exist_ok=True)
	os.makedirs(LOGGING_DIR, exist_ok=True)
	os.makedirs(TEMP_DIR, exist_ok=True)

def easy_run():
	parser = argparse.ArgumentParser("--")
	parser.add_argument("--run", type=str)	# e.g. "esg_crawler", "esg_downloader", "csdn_watcher_and_reader"
	parser.add_argument("--category", type=str)	# e.g. "report", "event", "penalty"
	parser.add_argument("--start_page", type=int)	# @param start_page of `run_esg_crawler`
	parser.add_argument("--start_from", type=int)	# @param start_from of `run_esg_downloader`
	parser.add_argument("--monitor_interval", type=int)	# @param watch_interval of `run_csdn_monitor`
	parser.add_argument("--n_days_before", type=int)	# @param n_days_before of `run_csdn_displayer`
	parser.add_argument("--paper_dir", type=str)	# @param 
	args = parser.parse_args()
	kwargs = dict()
	for key, word in args._get_kwargs():
		if key == "run":
			logging_prefix = word
			function = eval(f"run_{word}")
		else:
			kwargs[key] = word
	make_directories()
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/{logging_prefix}_{time_string}.log")
	function(**kwargs)
	terminate_logger(logger)

def run_esg_crawler(category, start_page, **kwargs):
	esg = ESGCrawler()
	while True:
		current_page = esg.parse_tables_over_pages(category,
												   start_page,
												   start_row = 0,
												   browser = "chrome",
												   headless = False,
												   timeout = 60,
												   )
		
		start_page = current_page + 1
		logging.info(f"Restart at {start_page} ...")
		
def run_esg_downloader(category, start_from, **kwargs):
	esg = ESGCrawler()
	esg.download_reports(category,
						 start_from,
						 download_interval = 20, 
						 )

def run_csdn_monitor(monitor_interval, **kwargs):
	csdn = CSDNCrawler()
	csdn.monitor_user_data(domain = "caoyang",
						   username = "CY19980216",
						   watch_article_ids = None,
						   read_article_ids = None,
						   max_view_count = 10000,
						   monitor_interval = monitor_interval,
						   )

def run_csdn_displayer(n_days_before, **kwargs):
	csdn = CSDNCrawler()
	csdn.display_watch_article_data(watch_article_ids = None,
									columns = ["view_count"],
									n_days_before = n_days_before,
									)

def run_aclanthology_downloader(paper_dir, **kwargs):
	aclanthology = ACLAnthologyCrawler()
	h = r"D:\code\python\project\caoyang\project_014_mrc\reference\conference"
	for root, dirnames, filenames in os.walk(root):
		for filename in filenames:
			if filename.endswith(".pdf"):
				paper_id = filename[: -4]
				aclanthology.download_paper_detail(paper_id, save_dir = os.path.join(CRAWLER_DATA_DIR, "aclanthology"))					

def run_bilibili_downloader(**kwargs):
	bbc = BilibiliCrawler()
	# bbc.easy_download_video(bvid="BV1N94y1P7Si")	# Accessible
	# bbc.easy_download_episode(ep_id="ep247270")	# 2024/12/28 03:51:26 Unavailable now
	# bbc.download(bvid = "BV11g411A7zx")	# Accessible
	# bbc.easy_download(url = "https://www.bilibili.com/bangumi/play/ep399420")	# Accessible
	# bbc.easy_download(url = "https://www.bilibili.com/bangumi/play/ep247270")	# Accessible
	bbc.easy_download(url = "https://www.bilibili.com/video/BV1B39EYdE1o")	# Accessible

def run_qidian_downloader(**kwargs):
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/qidian_downloader_{time_string}.log")
	qdc = QidianCrawler()
	book_url = "https://www.qidian.com/book/1042107497/"
	book = qdc.parse_book(book_url)
	terminate_logger(logger)

def run_bqg_downloader(**kwargs):
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/bqg128_downloader_{time_string}.log")
	bqg = BQG128Crawler()

	book_urls = [
		# "https://www.bqg128.com/book/51676/",	# dpcqyzsn
		# "https://www.bqg128.com/book/69296/",	# ylzf
		# "https://www.bqg128.com/book/170405/",	# jcxl
		# "https://www.bqg128.com/book/8885/", # hrxl
		# "https://www.bqg128.com/book/6692/", # smcnxl
		"https://www.bqg128.com/book/82229/",
		"https://www.bqg128.com/book/6625/",
		"https://www.bqg128.com/book/55170/",
		"https://www.bqg128.com/book/42323/",
		"https://www.bq02.cc/kan/80452/",
		"https://www.bqg128.com/book/26967/",
		"https://www.bqg128.com/book/13131/",
		"https://www.bqg128.com/book/47076/",
		"https://www.bqg128.com/book/39514/",
		"https://www.bqg128.com/book/7636/",
		"https://www.bqg128.com/book/20964/",
	]

	book_urls = [
		"https://www.bqg128.com/book/15001/",
		"https://www.bqg128.com/book/2983/",
		"https://www.bqg128.com/book/7088/",
		"https://www.bqg128.com/book/83975/",
		"https://www.bqg128.com/book/105360/",
		"https://www.bqg128.com/book/109419/",
		"https://www.bqg128.com/book/8591/",
		"https://www.bqg128.com/book/70331/",
		"https://www.bqg128.com/book/61424/",
		"https://www.bqg128.com/book/102027/",
		"https://www.bqg128.com/book/95041/",
		"https://www.bqg128.com/book/141684/",
		"https://www.bqg128.com/book/95489/",
		"https://www.bqg128.com/book/116850/",
		"https://www.bqg128.com/book/108352/",
		"https://www.bqg128.com/book/13112/",
	]
	book_urls = [
		# "https://www.bqg128.com/book/42558/", # zeds-njly
		"https://www.bqg128.com/book/24031/",
		"https://www.bqg128.com/book/72728/",
		"https://www.bqg128.com/book/109747/",
		"https://www.bqg128.com/book/18497/",
		"https://www.bqg128.com/book/71900/",
		"https://www.bqg128.com/book/106595/",
		"https://www.bqg128.com/book/84381/",
		"https://www.bqg128.com/book/105865/",
		"https://www.bqg128.com/book/138474/",
	]
	book_urls = [
		"https://www.bqg128.com/book/138474/",
	]
	for book_url in book_urls:
		logging.info(f"Download: {book_url.rstrip('/').split('/')[-1]}")
		book = bqg.parse_book(book_url, interval = 2)
	terminate_logger(logger)	

def run_bqg_top_downloader():
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/bqg128_top_downloader_{time_string}.log")
	bqg = BQG128Crawler()
	top_books = bqg.parse_top_books()
	import json
	from pprint import pprint
	from urllib.request import urljoin
	pprint(top_books)
	with open("./top.json", 'w', encoding="utf8") as f:
		json.dump(top_books, f, ensure_ascii=False)
	for category, books in top_books.items():
		logging.info(f"Category: {category}")
		for book in books:
			book_name = book["bookName"]
			book_url = urljoin(bqg.url_host, book["bookURL"])
			logging.info(f"Download {book_name}: {book_url.rstrip('/').split('/')[-1]}")
			book = bqg.parse_book(book_url, interval = 2)
	terminate_logger(logger)	

def run_bixia_downloader(**kwargs):
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/bixia_downloader_{time_string}.log")
	bixia = Bxwxx7Crawler()
	book_urls = [
		"https://www.bxwxx7.com/article/122858/", # qcxhbcrc
	]
	for book_url in book_urls:
		logging.info(f"Download: {book_url.rstrip('/').split('/')[-1]}")
		book = bixia.parse_book(book_url, interval = 2)
	terminate_logger(logger)	
	
def run_77shu_downloader(**kwargs):
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/77shu_downloader_{time_string}.log")
	shu77 = Shu77Crawler()
	book_urls = [
		"https://www.77shu.com/xiaoshuo/167621/", # qcxhbcrc
	]
	for book_url in book_urls:
		logging.info(f"Download: {book_url.rstrip('/').split('/')[-1]}")
		book = shu77.parse_book(book_url, interval = 2)
	terminate_logger(logger)	

def run_kuwo_downloader(**kwargs):
	kuwo = KuwoCrawler()
	kuwo.easy_download(mid="32673026")	


def run_netease_download(**kwargs):
	netease = NeteaseCrawler()
	netease.easy_download(song_id="1922872670")

if __name__ == "__main__":
	# easy_run()	# bash script trigger
	# run_aclanthology_downloader()
	# run_bilibili_downloader()
	# run_qidian_downloader()
	# run_bqg_downloader()
	# run_bqg_top_downloader()
	# run_bixia_downloader()
	# run_77shu_downloader()
	run_kuwo_downloader()
	# run_netease_download()
