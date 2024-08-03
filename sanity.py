# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

import sys
import argparse

def f(a, **kwargs):
	print(a)
	print(kwargs)




if __name__ == "__main__":
	# parser = argparse.ArgumentParser("--")
	# parser.add_argument("--category", type=str)
	# args = parser.parse_args()
	# print(args._get_kwargs())
	# print(dir(args))
	# for k, v in args:
		# print(k, v)
	# print(sys.argv)

	params = {"a": 1, "b": 2}
	f(**params)
	
