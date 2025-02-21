# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import re
import time
import logging
import requests

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from src.base import BaseClass

class BaseCrawler(BaseClass):
	reset_interval = 300
	click_interval = 3
	chrome_user_data_path = r"C:\Users\caoyang\AppData\Local\Google\Chrome\User Data"
	regexes = {"html_tag": re.compile(r"<[^>]+>|\n|\t"),	# Remove HTML tags, including '\t' and '\n'
			   "br": re.compile(r"<br>|<br/>"),	# Replace <br> or <br/> to '\n'
			   "forbidden_filename_char": re.compile(r"\\|/|:|\?|\*|\"|<|>|\|"),	# Characters which are forbidden in filename (on WINDOWS system)
			   "number": re.compile(r"\d+"),	# Extract number
			   "host": re.compile("https://(.*\.com)"),	# Extract host-like string
			   }
	javascript = {"scroll_into_view": "arguments[0].scrollIntoView(true);",
				  "scroll_into_view_center": "arguments[0].scrollIntoView({behavior: \"instant\", block: \"center\", inline: \"center\"});",
				  }

	def __init__(self, **kwargs):
		super(BaseCrawler, self).__init__(**kwargs)
	
	# Convert request headers copied from Firefox to dictionary
	# @param headers: Headers string
	@classmethod
	def headers_to_dict(cls, headers: str) -> dict:
		lines = headers.splitlines()
		headers_dict = {}
		for line in lines:
			key, value = line.strip().split(':', 1)
			headers_dict[key.strip()] = value.strip()
		return headers_dict

	# Easy use of WebDriverWait
	# @param driver: Browser driver
	# @param xpath: XPath of the checked element
	# @param timeout: Timeout of `WebDriverWait`
	@classmethod
	def check_element_by_xpath(cls,
							   driver,
							   xpath,
							   timeout = 30,
							   ):
		logging.info(f"Check XPath: {xpath}")
		WebDriverWait(driver, timeout).until(lambda _driver: _driver.find_element_by_xpath(xpath).is_displayed())
		logging.info(f"XPath {xpath} is visible!")
	
	# @param method: e.g. GET, POST
	# @param url: Requested URL
	# @param max_trial: Max request times
	def easy_requests(self, 
					  method, 
					  url, 
					  max_trial = 5, 
					  **kwargs,
					  ):
		count = 0
		while True:
			try:
				response = requests.request(method, url, **kwargs)
				break
			except Exception as e:
				count += 1
				logging.warning(f"Error {method} {url}, exception information: {e}")
				logging.warning(f"Wait for {self.reset_interval} seconds ...")
				if count == max_trial:
					logging.warning(f"Exceed max trial times: {max_trial}")
					return
				time.sleep(self.reset_interval)
		return response

	# Initialize driver
	# @param driver: Browser driver
	# @param headless: Whether to use headless driver
	# @param timeout: Global driver timeout
	# @return: Browser driver
	def initialize_driver(self, 
						  browser = "chrome", 
						  headless = True, 
						  timeout = 60, 
						  **kwargs,
						  ):
		browser = browser.lower()
		assert browser in ["chrome", "firefox"], f"Unknown browser name: {browser}"
		return eval(f"self._initialize_{browser}_driver")(headless, timeout, **kwargs)
	
	# Initialize Google Chrome driver
	def _initialize_chrome_driver(self, 
								  headless, 
								  timeout, 
								  **kwargs,
								  ):
		chrome_options = webdriver.ChromeOptions()		
		chrome_options.add_argument(f"user-data-dir={self.chrome_user_data_path}")	# Import user data
		if headless:
			chrome_options.add_argument("--headless")
		driver = webdriver.Chrome(chrome_options=chrome_options)
		driver.set_page_load_timeout(timeout)
		if not headless:
			driver.maximize_window()
		return driver

	# Initialize Mozilla Firefox driver
	def _initialize_firefox_driver(self, 
								   headless, 
								   timeout, 
								   **kwargs,
								   ):
		options = webdriver.FirefoxOptions()
		if headless:
			options.add_argument("--headless")
		driver = webdriver.Firefox(options=options)
		driver.set_page_load_timeout(timeout)
		if not headless:
			driver.maximize_window()
		return driver

	# Get cookies by driver
	# @param url: Target URL
	# @param driver: Browser driver
	# @param browser: Browser name, e.g. "chrome", "firefox"
	# @return: Cookie string
	def get_cookies(self, 
					url, 
					driver = None, 
					browser = "chrome",
					):
		quit_flag = False
		if driver is None:
			# If there is no driver passed
			quit_flag = True
			driver = self.initialize_driver(browser=browser, headless=True, timeout=30)
		driver.get(url)
		cookies = driver.get_cookies()
		def _cookie_to_string(_cookies):
			_string = str()
			for _cookie in _cookies:
				_name = _cookie["name"]
				_value = _cookie["value"].replace(' ', "%20") # %20 refers to space char in HTML
				_string += f"{_name}={_value};"
			return _string.strip()
		if quit_flag:
			driver.quit()
		return _cookie_to_string(cookies)

	# @param string: Str, string contained nest structure
	# @param nest_symbol: Tuple, e.g. ('(', ')'), ('[', ']'), ('{', '}')
	# @param start_at: Int, search start index
	# @param max_return: Int, The maximum number of parsed results
	@classmethod
	def easy_match_nest_structure(cls, string, nest_symbol, start_at = 0, max_return = -1):
		matched_nest_structures = list()
		matched_string = None
		count = None
		index = start_at - 1
		while index < len(string) - 1:
			index += 1
			if count is None:
				if string[index] == nest_symbol[0]:
					# Start!
					matched_string = string[index]
					count = 1
				else:
					# Not start yet
					continue
			else:
				matched_string += string[index]
				# Start already
				if string[index] == nest_symbol[0]:
					count += 1
				elif string[index] == nest_symbol[1]:
					count -= 1
					if count == 0:
						# Matched already
						matched_nest_structures.append(matched_string)
						if len(matched_nest_structures) == max_return:
							return matched_nest_structures
						matched_string = None
						count = None
		return matched_nest_structures