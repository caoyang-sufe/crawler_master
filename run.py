# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import sys
import time
import argparse

from src.crawlers import ESGCrawler, CSDNCrawler, ACLAnthologyCrawler, BilibiliCrawler
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
	# bbc.easy_download_video(bvid="BV11g411A7zx")	# Accessible
	# bbc.easy_download_episode(ep_id="ep247270")	# 2024/12/28 03:51:26 Unavailable now
	# bbc.download(bvid = "BV11g411A7zx")	# Accessible
	# bbc.easy_download(url = "https://www.bilibili.com/video/BV1jf4y1h73r")	Accessible
	# bbc.easy_download(url = "https://www.bilibili.com/bangumi/play/ep399420")	# Accessible
	# bbc.easy_download(url = "https://www.bilibili.com/bangumi/play/ep247270")	# Accessible

if __name__ == "__main__":
	# easy_run()	# bash script trigger
	# run_aclanthology_downloader()
	run_bilibili_downloader()