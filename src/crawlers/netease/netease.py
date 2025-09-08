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

class NetEase(object):
	"""
	Download music from [NetEase Online](https://music.163.com/)
	"""
	def __init__(self) -> None:			
		self.url_main = 'https://music.163.com/'
		self.headers = {'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0'}
		self.url_api = self.url_main + 'weapi/song/enhance/player/url?csrf_token='
		self.url_song = self.url_main + 'song?id={}'
		self.url_search = self.url_main + 'search/m/?s={}'
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
		driver.get(self.url_main)
		xpath_input_frame = '//input[@id="srch"]'
		input_frame = driver.find_element_by_xpath(xpath_input_frame)
		input_frame.send_keys(song_name)
		input_frame.send_keys(Keys.ENTER)
		driver.switch_to_frame('g_iframe')
		WebDriverWait(driver, 15).until(lambda driver: driver.find_element_by_xpath('//div[@class="srchsongst"]').is_displayed())
		html = driver.page_source
		soup = BeautifulSoup(html, 'lxml')
		result_list = soup.find('div', class_='srchsongst')
		divs = list(result_list.children)[:n_result]
		song_ids = []
		for div in divs:
			div.find('div', class_='td')
			a = div.find('a')
			song_id = a.attrs['id'][5:]
			song_ids.append(song_id)
		driver.quit()
		return song_ids

	def download_by_song_id(self, song_id: str, save_path: str=None, driver: webdriver.Firefox=None) -> None:
		"""
		Download the song by id and write it into local file. 
		"""
		song_url = self.request_for_song_url(song_id, driver=driver)	
		r = self.session.get(song_url)									
		if save_path is None: 
			save_path = 'netease_{}'.format(song_id)					
		with open(save_path, 'wb') as f: 
			f.write(r.content)											


	def request_for_song_url(self, song_id: str, driver: webdriver.Firefox=None) -> str:
		"""
		Get the resource URL of the song needed to be downloaded. 
		"""
		formdata = self.encrypt_formdata(song_id, driver=driver)		
		r = self.session.post(self.url_api, data=formdata)				
		song_url = json.loads(r.text)['data'][0]['url']					
		return song_url

		
	def encrypt_formdata(self, song_id: str, driver: webdriver.Firefox=None) -> dict:
		"""
		Encrypt the formdata by the logic in NetEase javascript.
		Note that the formdata post to download music is encrypted.
		"""
		d='{"ids":"[%s]","br":128000,"csrf_token":""}'			
		e='010001'									
		f='00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
		g='0CoJUm6Qyw8W8jud'									
		d %= song_id													
		if driver is not None:											
			JS = 'return window.asrsea("{}", "{}", "{}", "{}")'.format(d, e, f, g)
			driver.get(self.url_song.format(song_id))
			formdata = driver.execute_script(JS)						
			formdata = dict(params=formdata['encText'], encSecKey=formdata['encSecKey'])
			return formdata
			
		def _javascript2python_a(a):									
			b = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
			c = str()
			for i in range(a): c += b[math.floor(random.random()*len(b))]
			return c
 
		def _javascript2python_b(a, b):									
			pad = 16 - len(a.encode())%16								
			a += pad * chr(pad)											
			encryptor = AES.new(b.encode('UTF-8'), AES.MODE_CBC, b'0102030405060708')	
			f = base64.b64encode(encryptor.encrypt(a.encode('UTF-8')))
			return f
			
		def _javascript2python_c(a, b, c):								
			b = b[::-1]													
			e = int(codecs.encode(b.encode('UTF-8'), 'hex_codec'), 16)**int(a,16) % int(c,16)
			return format(e, 'x').zfill(256)							
 
		random_text = _javascript2python_a(16)							
		params = _javascript2python_b(d, g)								
		params = _javascript2python_b(params.decode('UTF-8'), random_text)
		encSecKey = _javascript2python_c(e, random_text, f)				
		formdata = dict(params=params, encSecKey=encSecKey)				
		return formdata													
 
	def test(self):
		song_id = '1922872670'
		r = self.download_by_song_id(
			song_id,
			save_path='netease_{}.mp3'.format(song_id),
			driver=None,
		)

	def test_batch(self):
		data = {
			"1039314": "书中有",
		}
		for song_id, title in data.items():
			r = self.download_by_song_id(
				song_id,
				save_path=title+'.mp3',
				driver=None,
			)			

if __name__ == "__main__":

	ne = NetEase()
	ne.test()
	# ne.test_batch()
