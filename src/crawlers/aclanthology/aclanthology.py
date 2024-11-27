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

from src.crawlers.csdn import CRAWLER_NAME
from src.crawlers.base import BaseCrawler

from settings import CRAWLER_DATA_DIR, TEMP_DIR


class ACLAnthologyCrawler(BaseCrawler):
	url_host = "https://aclanthology.org/"
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

	def __init__(self,
				 **kwargs,
				 ):
		super(ACLAnthologyCrawler, self).__init__(**kwargs)
		self.monitor_save_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, "monitor")	# Save the monitor data
		os.makedirs(self.monitor_save_dir, exist_ok=True)

