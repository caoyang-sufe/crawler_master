# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import argparse
from copy import deepcopy

class BaseConfig:
	parser = argparse.ArgumentParser("--")
	parser.add_argument("--chrome_user_data_path", 
						default = r"C:\Users\caoyang\AppData\Local\Google\Chrome\User Data",
						type = str,
						)

class ESGConfig:
	parser = deepcopy(BaseConfig)

class CSDNConfig:
	parser = deepcopy(BaseConfig)
