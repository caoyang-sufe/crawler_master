# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import os
import time
import random
import pandas
import logging
from bs4 import BeautifulSoup
from urllib.request import urljoin
from selenium.webdriver.common.action_chains import ActionChains

from src.crawlers.base import BaseCrawler
from src.crawlers.esg import CRAWLER_NAME

from settings import CRAWLER_DATA_DIR, TEMP_DIR

class ESGCrawler(BaseCrawler):
	url_host = "https://i-esg.com"
	url_esg_summary = {"report": urljoin(url_host, "/esg/esgReport"),
					   "event": urljoin(url_host, "/esgEvent/event/ag"),
					   "penalty": urljoin(url_host, "/environmentCredit/environmentPenalties")
					   }
	jump_size = 5
	click_interval = 2
	max_trial = 5
	xpaths = {
		"table_header": "//table[@class=\"vxe-table--header\"]",	# <table> which contains the table header
		"table_body": "//table[@class=\"vxe-table--body\"]",		# <table> which contains the table body
		"report_link_report": "//a[@class=\"line-clamp-1\"]",	# <a> which links to the report of report (may be in form of PDF, WORD, HTML, ZIP packages)
		"report_link_penalty": "//table[@class=\"vxe-table--body\"]//td[not(contains(@class, \"fixed--hidden\"))]//a[@class=\"line-clamp-1\"]",	# Note: There are two tables matching XPATH `//table[@class=\"vxe-table--body\"]` on the page
		"report_link_event": "//tr/td[3]//a",	# <a> which links to the report of event (may be in form of PDF, WORD, HTML, ZIP packages)
		"next_page_button": "//button[@class=\"vxe-pager--next-btn\"]",	# <button> which is clicked to next page
		"last_page_button": "//button[@class=\"vxe-pager--prev-btn\"]",	# <button> which is clicked to last page
		"jump_right_button": "//button[@class=\"vxe-pager--jump-next\"]",	# <button> which is clicked to jump 5 pages behind
		"jump_left_button": "//button[@class=\"vxe-pager--jump-prev\"]",	# <button> which is clicked to jump 5 pages before
		"current_page_button": "//button[@class=\"vxe-pager--num-btn is--active\"]",	# <button> which shows the current page number (unique)
		"other_page_button": "//button[@class=\"vxe-pager--num-btn\"]",					# <button> which shows other page numbers (many)
		"scroll_to_top_icon": "//i[@class=\"vc-icon ico-bx:arrow-to-top iconfont\"]",	# <i> which is clicked to return to the top of the report table
		"pdf_id_span": "//span[@id=\"title\"]",	# <span> which contains the pdf id (i.e. filename)
		"report_iframe": "//iframe[@class=\"vc-iframe-page\"]",	# <iframe> which contains the report PDF content
		"pdf_download_div": "//viewer-download-controls[@id=\"download\"]",	# <div> which contains the download button
		"pdf_download_button": "//cr-icon-button[@id=\"download\"]",		# <button> which is clicked to download PDF
		"alert_div": "//div[@slot=\"body\"]",	# <div> which contains the alerting text which indicates that the PDF is not successfully loaded
		"alert_button": "//cr-button[@class=\"action-button\"]",	# <cr-button> which is clicked to reload the page in alert box
		"close_span": "//div[@class=\"vc-tabs__item is-top is-active is-closable\"]//span[@class=\"is-icon-close\"]",	# <span> which is clicked to close the active tab
		"content_div": "//div[@class=\"zlibDetailWrapper\"]",	# <div> which contains the content of the report which is not PDF. You can directly fetch the text on the active tab
	}

	def __init__(self, 
				 **kwargs,
				 ):
		super(ESGCrawler, self).__init__(**kwargs)

	# Unified function to parse tables over several pages
	# @param category: Key of `self.url_esg_summary`, e.g. "report", "event", "penalty"
	# @param start_page: Page which starts at
	# @param start_row: Page which starts at
	# @param browser: Browser name, e.g. "chrome", "firefox"
	# @param headless: Whether to use headless driver
	# @param timeout: Browser driver timeout
	def parse_tables_over_pages(self,
								category,
								start_page = 1,
								start_row = 0,
								browser = "chrome",
								headless = False,
								timeout = 60,
								):
		# Global definition
		url_esg = self.url_esg_summary[category]
		iframe_save_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, category, "iframe")	# PDF, WORD
		html_save_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, category, "html")	# HTML
		os.makedirs(iframe_save_dir, exist_ok=True)
		os.makedirs(html_save_dir, exist_ok=True)
		detail_save_path = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, category, "detail.txt")	# Save the return of `_easy_parse_report_link`
		table_save_path = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, category, "table.txt")	# Save the return of `_easy_parse_esg_table`
		# Start chrome driver
		driver = self.initialize_driver(browser = browser,
										headless = headless,
										timeout = timeout,
										)
		try:
			driver.get(url_esg)	# Visit the first page
			BaseCrawler.check_element_by_xpath(driver, xpath=self.xpaths["table_body"])	# Check if table is loaded
			current_page = self._easy_get_current_page_number(driver)	# Determine current page number
			current_page = self._easy_skip_to_target_page(driver,
														  current_page,
														  target_page = start_page,
														  jump_size = self.jump_size,
														  click_interval = self.click_interval,
														  )
			logging.info(f"Start at page {start_page}, currently at {current_page}")
			assert start_page == current_page
			while True:
				current_page = self._easy_get_current_page_number(driver)	# Determine current page number
				logging.info(f"Current Page: {current_page}")
				# Parse table data
				esg_dataframe = self._easy_parse_esg_table(driver, save_path = table_save_path)
				# Parse detailed report content
				logging.info("Fetch report links ...")
				report_links = driver.find_elements_by_xpath(self.xpaths[f"report_link_{category}"])
				logging.info(f"  - Done! Totally {len(report_links)}")
				for current_row, report_link in enumerate(report_links):
					if current_page == start_page and current_row < start_row:
						continue
					parsed_results = self._easy_parse_report_link(driver, report_link)
					self._easy_save_detail_results(parsed_results,
												   detail_save_path,
												   html_save_dir,
												   )
				self._easy_turn_over_page_and_scroll_back(driver,
														  click_interval = self.click_interval,
														  )
		except Exception as exception:
			driver.quit()
			logging.info("Global Exception:")
			logging.info(str(exception).replace('\n', ';'))
			time.sleep(300)
			return current_page
		driver.quit()
		
	# Download reports according to `detail_save_path`
	# @param category: Key of `self.url_esg_summary`, e.g. "report", "event", "penalty"
	# @param start_from: Index number of `detail_save_path` which is started from
	# @param download_interval: Expected interval between two downloads
	def download_reports(self,
						 category,
						 start_from = 0,
						 download_interval = 15,
						 ):
		iframe_save_dir = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, category, "iframe")
		detail_save_path = os.path.join(CRAWLER_DATA_DIR, CRAWLER_NAME, category, "detail.txt")
		interval_lower = download_interval // 2
		interval_upper = download_interval // 2 * 3
		dataframe_detail = pandas.read_csv(detail_save_path, sep='\t', header=0, dtype=str, encoding="utf8")
		dataframe_detail.fillna(str(), inplace=True)	
		for i in range(start_from, dataframe_detail.shape[0]):
			title = dataframe_detail.loc[i, "title"]
			download_url = dataframe_detail.loc[i, "download_url"]
			text = dataframe_detail.loc[i, "text"]
			error = dataframe_detail.loc[i, "error"]
			logging.info(f"Download reports: {title}")
			if download_url:
				self._easy_download_iframe(download_url, iframe_save_dir)
				time.sleep(random.randint(interval_lower, interval_upper))
			else:
				if text:
					logging.info("  - This is HTML text!")
				elif error:
					logging.info("  - This is ClickToDownload (ZIP Package maybe)!")

	# Get the current page number in `current_page_button`
	# @param driver: Browser driver
	def _easy_get_current_page_number(self, driver):
		current_page_button = driver.find_element_by_xpath(self.xpaths["current_page_button"])
		current_page_button_html = current_page_button.get_attribute("outerHTML")
		current_page_button_string = self.regexes["html_tag"].sub(str(), current_page_button_html)
		current_page_number = int(current_page_button_string)
		return current_page_number
	
	# Sometimes we need to parse from the intermediate page
	# Quickly skip from current page to target page
	# @param driver: Browser driver
	# @param current_page: Current page number 
	# @param target_page: Target page number
	# @param jump_size: How many pages skipped when clicking `jump_right_button` or `jump_left_button`
	# @param click_interval: Global interval after clicking elements
	# @return current_page: The page number actually skipped to
	def _easy_skip_to_target_page(self,
								  driver,
								  current_page,
								  target_page,
								  jump_size = 5,
								  click_interval = 2,
								  ):
		logging.info(f"Skip from {current_page} to {target_page}")
		skip_strategy = {"next": 0, "last": 0, "jump_right": 0, "jump_left": 0}
		difference = target_page - current_page
		if difference > 0:
			skip_strategy["next"] = difference % jump_size
			skip_strategy["jump_right"] = difference // jump_size
		else:
			skip_strategy["last"] = - difference % jump_size
			skip_strategy["jump_left"] = - difference // jump_size
		logging.info(f"Skip strategy: {skip_strategy}")
		if skip_strategy["next"]:
			logging.info("Scrolling to the bottom to find `next_page_button` ...")
			next_page_button = driver.find_element_by_xpath(self.xpaths["next_page_button"])
			driver.execute_script(self.javascript["scroll_into_view"], next_page_button)
			time.sleep(click_interval)
			logging.info("  - Done!")
			for _ in range(skip_strategy["next"]):
				logging.info("Click to the next page ...")
				next_page_button = driver.find_element_by_xpath(self.xpaths["next_page_button"])
				next_page_button.click()
				time.sleep(click_interval)
				current_page = self._easy_get_current_page_number(driver)
				logging.info(f"Turn to {current_page}!")
		if skip_strategy["last"]:
			logging.info("Scrolling to the bottom to find `last_page_button` ...")
			last_page_button = driver.find_element_by_xpath(self.xpaths["last_page_button"])
			driver.execute_script(self.javascript["scroll_into_view"], last_page_button)
			time.sleep(click_interval)
			logging.info("  - Done!")
			for _ in range(skip_strategy["last"]):
				logging.info("Click to the last page ...")
				last_page_button = driver.find_element_by_xpath(self.xpaths["last_page_button"])
				last_page_button.click()
				time.sleep(click_interval)
				current_page = self._easy_get_current_page_number(driver)
				logging.info(f"Turn to {current_page}!")
		if skip_strategy["jump_right"]:
			logging.info("Scrolling to the bottom to find `jump_right_button` ...")
			jump_right_button = driver.find_element_by_xpath(self.xpaths["jump_right_button"])
			driver.execute_script(self.javascript["scroll_into_view"], jump_right_button)
			time.sleep(click_interval)
			logging.info("  - Done!")
			for _ in range(skip_strategy["jump_right"]):
				logging.info(f"Jump to the {jump_size} page behind ...")
				jump_right_button = driver.find_element_by_xpath(self.xpaths["jump_right_button"])
				ActionChains(driver).move_to_element(jump_right_button).click().perform()
				time.sleep(click_interval)
				current_page = self._easy_get_current_page_number(driver)
				logging.info(f"Turn to {current_page}!")
		if skip_strategy["jump_left"]:
			logging.info("Scrolling to the bottom to find `jump_left_button` ...")
			jump_left_button = driver.find_element_by_xpath(self.xpaths["jump_left_button"])
			driver.execute_script(self.javascript["scroll_into_view"], jump_left_button)
			time.sleep(click_interval)
			logging.info("  - Done!")
			for _ in range(skip_strategy["jump_left"]):
				logging.info(f"Jump to the {jump_size} page before ...")
				jump_left_button = driver.find_element_by_xpath(self.xpaths["jump_left_button"])
				ActionChains(driver).move_to_element(jump_left_button).click().perform()
				time.sleep(click_interval)
				current_page = self._easy_get_current_page_number(driver)
				logging.info(f"Turn to {current_page}!")
		logging.info("Finish skipping!")
		if current_page == target_page:
			logging.info(f"Successfully skip to start page {target_page}")
		else:
			logging.warning(f"Fail in skipping start page {target_page}, currently at {current_page}")
		return current_page

	# Parse all the data list in the table on one page
	# @param driver: Browser driver
	# @param save_path: Table DataFrame save path, i.e. `table_save_path`
	# @return esg_dataframe: Full table data transferred to DataFrame
	def _easy_parse_esg_table(self, 
							  driver,
							  save_path = None,
							  ):
		# Parse table header
		table_header = driver.find_element_by_xpath(self.xpaths["table_header"])
		table_header_html = table_header.get_attribute("outerHTML")
		table_header_soup = BeautifulSoup(table_header_html, "html.parser")
		th_tags = table_header_soup.find_all("th")
		columns = list()
		for th_tag in th_tags:
			columns.append(self.regexes["html_tag"].sub(str(), str(th_tag)))
		columns_length = len(columns)
		# Parser table body
		table_body = driver.find_element_by_xpath(self.xpaths["table_body"])
		table_body_html = table_body.get_attribute("outerHTML")
		table_body_soup = BeautifulSoup(table_body_html, "html.parser")
		esg_json = {column: list() for column in columns}
		tr_tags = table_body_soup.find_all("tr")
		for tr_tag in tr_tags:
			td_tags = tr_tag.find_all("td")
			data = list()
			for td_tag in td_tags:
				data.append(self.regexes["html_tag"].sub(str(), str(td_tag)))
			data_length = len(data)
			if columns_length != data_length:
				logging.warning(f"Length mismatch between table header({columns_length}) and row({data_length})!")
				if columns_length < data_length:
					data = data[: columns_length]
				else:
					data += [str()] * (columns_length - data_length)
			for column, datum in zip(columns, data):
				esg_json[column].append(datum)
		esg_dataframe = pandas.DataFrame(esg_json, columns=columns)
		if save_path is not None:
			if os.path.exists(save_path):
				temp_save_path = os.path.join(TEMP_DIR, ".tmptab")
				esg_dataframe.to_csv(temp_save_path, sep='\t', header=False, index=False, encoding="utf8")
				with open(temp_save_path, 'r', encoding="utf8") as f:
					esg_dataframe_string = f.read()
				with open(save_path, 'a', encoding="utf8") as f:
					f.write(esg_dataframe_string)
			else:
				esg_dataframe.to_csv(save_path, sep='\t', header=True, index=False, encoding="utf8")
		return esg_dataframe

	# Parse the detailed content of one report
	# Download PDF, WORD or ZIP packages or simply parse the HTML content
	# @param driver: Browser driver
	# @param report_link: Report link element found by XPATH
	# @param click_interval: Global interval after clicking elements
	# @return: Dict[title, download_url, text, error]
	def _easy_parse_report_link(self, 
								driver,
								report_link,
								click_interval = 2,
								):
		report_download_url = str()
		report_text = str()
		error = str()
		report_link_html = report_link.get_attribute("outerHTML")
		report_title = self.regexes["html_tag"].sub(str(), report_link_html)
		logging.info(f"Click into report: {report_title}")
		n_trial = 0
		while True:
			try:
				report_link.click()	# Click to view the report detail pages
				logging.info("  - Success!")
				time.sleep(click_interval)
				break
			except Exception as exception:
				n_trial += 1
				logging.info(f"  - Failure {n_trial}: {exception}")
				driver.execute_script(self.javascript["scroll_into_view_center"], report_link)
				time.sleep(click_interval)
				if n_trial == self.max_trial:
					return {"title": str(),
							"download_url": report_download_url,
							"text": report_text,
							"error": "MAXTRIAL",	
							}
		# Tips: How to deal with the report detail pages?
		# - There exists an iframe:
		#   - PDF: URL can be found in <iframe src=...>
		#   - DOC or DOCX: URL can also be found in <iframe src=...>, but you need to process the URL, see `easy_download_report_iframe` for details
		# - Otherwise:
		#   - HTML: Simply fetch the HTML text
		#   - ZIP package (Click to download, set auto download in Chrome or Firefox for convenience)
		#     - Note that in this case, you need not close the active tab
		# Judge if there exists an iframe on detail pages
		try:
			BaseCrawler.check_element_by_xpath(driver, xpath=self.xpaths["report_iframe"], timeout=5)
			flag_is_iframe = True
		except:
			flag_is_iframe = False
		if flag_is_iframe:
			# PDF, WORD
			logging.info("There exists an iframe")
			report_iframe = driver.find_element_by_xpath(self.xpaths["report_iframe"])
			report_iframe_html = report_iframe.get_attribute("outerHTML")
			report_iframe_soup = BeautifulSoup(report_iframe_html, "html.parser")
			report_download_url = report_iframe_soup.find("iframe").attrs["src"]
		else:
			logging.info("This is not an iframe")
			try:
				# HTML
				content_div =  driver.find_element_by_xpath(self.xpaths["content_div"])
				content_div_html = content_div.get_attribute("outerHTML")
				# report_text = self.regexes["html_tag"].sub(str(), content_div_html)
				report_text = content_div_html
			except Exception as exception:
				# ZIP Package (Usually)
				error = str(exception).replace('\n', ';')
		# Judge whether to close active tab after parse the report detail pages
		try:
			driver.find_element_by_xpath(self.xpaths["current_page_button"])
			logging.info("Need not close PDF!")
			flag_close_tab = False
		except:
			flag_close_tab = True
			logging.info("Need to close PDF!")
		if flag_close_tab:
			logging.info("  - Close report tab ...")
			driver.find_element_by_xpath(self.xpaths["close_span"]).click()
			logging.info("  - Done!")
			time.sleep(click_interval)
		return {"title": report_title,
				"download_url": report_download_url,	# PDF and WORD cases
				"text": report_text,	# HTML case
				"error": error,	# ZIP Package case
				}
	
	# Save the parsed detailed content, i.e. the returned results of `_easy_parse_report_link`
	# @param parsed_results: The return of `_easy_parse_report_link`
	# @param detail_save_path: Save path of `parsed_results`
	# @param html_save_dir: Directory to save HTML text
	def _easy_save_detail_results(self, 
								  parsed_results,
								  detail_save_path,
								  html_save_dir,
								  ):
		report_title = parsed_results["title"]
		pdf_download_url = parsed_results["download_url"]
		report_text = parsed_results["text"]
		error = parsed_results["error"]
		columns = list(parsed_results.keys())
		if not os.path.exists(detail_save_path):
			with open(detail_save_path, 'w', encoding="utf8") as f:
				f.write('\t'.join(columns) + '\n')
		if report_text:
			# Save content parsed from HTML text
			filename = self.regexes["forbidden_filename_char"].sub(str(), report_title)
			report_text_save_path = os.path.join(html_save_dir, f"{filename}.html")
			with open(report_text_save_path, 'w', encoding="utf8") as f:
				f.write(report_text)
			report_text = report_text_save_path
		with open(detail_save_path, 'a', encoding="utf8") as f:
			f.write('\t'.join([report_title, pdf_download_url, report_text, error]) + '\n')
			
	# Turn over page and scroll back to the top of the table
	# @param driver: Browser driver
	def _easy_turn_over_page_and_scroll_back(self, 
											 driver, 
											 click_interval,
											 ):
		logging.info("Scrolling to the bottom ...")
		next_page_button = driver.find_element_by_xpath(self.xpaths["next_page_button"])
		driver.execute_script(self.javascript["scroll_into_view"], next_page_button)
		logging.info("  - Done!")
		time.sleep(click_interval)
		logging.info("Click to the next page ...")
		next_page_button.click()
		logging.info("  - Done!")
		time.sleep(click_interval)
		logging.info("Scroll to the top ...")
		while True:
			try:
				BaseCrawler.check_element_by_xpath(driver, xpath=self.xpaths["scroll_to_top_icon"], timeout=10)
				scroll_to_top_icon = driver.find_element_by_xpath(self.xpaths["scroll_to_top_icon"])
				break
			except:
				logging.info("  - `scroll_to_top_icon` not found!")
				current_page_button = driver.find_element_by_xpath(self.xpaths["current_page_button"])
				driver.execute_script(self.javascript["scroll_into_view"], current_page_button)
				time.sleep(click_interval)
		scroll_to_top_icon.click()
		logging.info("  - Done!")
		time.sleep(click_interval)
		
	# Download PDF or WORD report by parsed URL
	# @param download_url: The return of `self._easy_parse_report_link`
	# @param iframe_save_dir: Save directory of PDF, WORD reports
	def _easy_download_iframe(self, 
							  download_url,
							  iframe_save_dir,
							  ):
		def _easy_deal_with_url(_url):
			_index = _url.find("?src=http")
			return _url if _index == -1 else _url[_index + 5: ]
		
		download_url = _easy_deal_with_url(download_url)
		response = self.easy_requests(method = "GET",
									  url = download_url,
									  max_trial = 5,
									  )
		if response is None:
			logging.info(f"Fail to download from {download_url}")
			return
		filename = download_url.split('/')[-1]
		save_path = os.path.join(iframe_save_dir, filename)
		logging.info(f"Save at {save_path}")
		with open(save_path, "wb") as f:
			f.write(response.content)
		logging.info("  - Done!")
