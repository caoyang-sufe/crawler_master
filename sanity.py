# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

class A:
	test = {}
	def __init__(self):
		pass


class B(A):
	def __init__(self,):

		super(B, self).__init__()

		self.test["asd"] = 1


b = B()

print(b.test)