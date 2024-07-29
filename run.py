# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import time

from src.crawlers import ESGCrawler
from src.tools.easy import initialize_logger, terminate_logger


def run_esg_crawler():
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/esg_crawler_{time_string}.log")
	# esg = ESGCrawler(category="report")
	esg = ESGCrawler(category="event")
	# esg = ESGCrawler(category="penalty")
	start_page = 1
	while True:
		current_page = esg.parse_tables_over_pages(start_page,
												   start_row = 0,
												   browser = "chrome",
												   headless = False,
												   timeout = 60,
												   )
		start_page = current_page + 1
	terminate_logger(logger)
	
	
def run_eag_downloader():
	time_string = time.strftime("%Y%m%d%H%M%S")
	logger = initialize_logger(f"./logging/esg_downloader_{time_string}.log")
	esg = ESGCrawler(category="report")
	esg.download_reports(detail_save_path = esg.detail_save_path,
						 download_interval = 20,
						 start_from = 67,
						 )
	terminate_logger(logger)
	

if __name__ == "__main__":
	run_esg_crawler()
	# run_eag_downloader()
