# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn
 
import os
import sys
import math
import time
import json
import random
import base64
import codecs

from requests import Session
from bs4 import BeautifulSoup
from Crypto.Cipher import AES											
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
 

class QQ(object):
	def __init__(self) -> None:
		self.url_main = 'https://y.qq.com/'								
		self.headers = {'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0'}
		self.url_song = self.url_main + 'n/yqq/song/{}.html'			
		self.url_js = 'https://y.gtimg.cn/music/portal/js/v4/player_d905eb5.js'
		self.url_link = 'http://{}/amobile.music.tc.qq.com/{}'			
 
		self.ips = [
			'180.153.119.147',
			'180.153.119.146',
			'180.153.119.144',
			'114.80.27.13',
		]
		self.renew_session()	
 
	def renew_session(self) -> None:
		"""
		Refresh the session in the class.
		"""
		self.session = Session()
		self.session.headers = self.headers.copy()
		self.session.get(self.url_main)
 
	def search_for_song_id(self, song_name: str, driver: webdriver.Firefox, n_result: int=1) -> list:
		"""
		Search the song ids for the given song name.
		Here the selenium driver is used because the search results of NetEase is in the <iframe>...</iframe> label which is hard to deal with by simple requests.
		
		:param song_name: Name of the song needed to search.
		:param driver: A browser driver initiated by selenium.
		:param n_result: Number of results returned, default 1 means select the top-1 search result.
		:return song_ids: List of song ids matching ```song_name```.
		"""
		raise NotImplementedError
		
	def download_by_song_id(self, song_id: str, save_path: str=None, driver: webdriver.Firefox=None) -> None:
		"""
		Download the song by id and write it into local file. 
		"""																
		song_url = self.request_for_song_url(song_id, driver=driver)	
		link_url = self.url_link.format(self.ips[0], song_url)
		r = self.session.get(link_url)									
		if save_path is None: 
			save_path = 'qq_{}'.format(song_id)		
		with open(save_path, 'wb') as f: 
			f.write(r.content)				
 
	def request_for_song_url(self, song_id: str, driver: webdriver.Firefox=None) -> str:
		"""
		Get the resource URL of the song needed to be downloaded. 
		Note that QQ Music is the most complex that selenium is needed to get the resource URL.
		"""																
		javascript = 'return window.g_vkey["{}"]'.format(song_id)				
		xpath_play_button = '//a[@class="mod_btn_green js_all_play"]'	
		driver.get(self.url_song.format(song_id))						
		time.sleep(2)
		driver.find_element_by_xpath(xpath_play_button).click()			
		windows = driver.window_handles									
		driver.switch_to.window(windows[-1])							
		xpath_hint = '//div[@id="divdialog_0"]'							
		if driver.find_elements_by_xpath(xpath_hint): 
			raise Exception('This song can only be played in client.')
		while True:
			try:
				result = driver.execute_script(javascript)						
				if result is None: 
					continue
				break
			except: 
				continue
		song_url = result['purl']					
		return song_url
 
	def test(self):
		options = webdriver.FirefoxOptions()							
		options.add_argument('--headless')								
		driver = webdriver.Firefox(options=options)						
		song_id = 'm9n8d42'										
		r = self.download_by_song_id(
			song_id,
			save_path='qq_{}.mp3'.format(song_id),
			driver=driver,
		)
		driver.quit()
 
if __name__ == "__main__":
	qq = QQ()
	qq.test()
 
 
