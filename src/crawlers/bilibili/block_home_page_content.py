# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chromedriver_path = r"C:\Program Files\Google\Chrome\Application\chromedriver.exe"
userdata_path = r"C:\Users\lzwcy\AppData\Local\Google\Chrome\User Data"
service = Service(executable_path=chromedriver_path)
options = webdriver.ChromeOptions()
options.binary_location = chrome_path
# options.add_argument(f"user-data-dir={userdata_path}")
# Useful options to avoid being discovered by website
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
# Common options
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
# Start driver
driver = webdriver.Chrome(service=service, options=options)
action = ActionChains(driver)
# driver.execute_script("Object.defineProperty(navigator, "webdriver", {get: () => undefined})")
# ----------------------------------------------------------------------
driver.get("https://www.bilibili.com")
svg_buttons = driver.find_elements(By.XPATH, './/svg[@class="bili-video-card__info--no-interest--icon"]')
dot_3_buttons = driver.find_elements(By.XPATH, './/div[@class="bili-video-card__info--right"]')
for button in dot_3_buttons[:6]:
	print(button)
	action.move_to_element_with_offset(button, 115, -30).pause(2).click().perform()	# Size: 240 × 65
	time.sleep(2)
	block_up_buttons = driver.find_elements(By.XPATH, './/div[@class="bili-video-card__info--no-interest-panel--item"]')	# Find two elements: 内容不感兴趣, 不想看此UP主
	print(block_up_buttons)
	action.move_to_element(block_up_buttons[0]).pause(1).click().perform()	
	time.sleep(2)
driver.quit()
