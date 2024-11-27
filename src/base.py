# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

class BaseClass:
	
	def __init__(self, **kwargs):
		for key, word in kwargs.items():
			self.__setattr__(key, word)
