# -*- coding: utf-8 -*-
# @author: caoyang
# @email: caoyang@stu.sufe.edu.cn

fp = "./logging/esg_20240726234759.log"

with open(fp, 'r', encoding="utf8") as f:
	line = -1
	while True:
		line += 1
		print(line, f.readline()[:-1])
		if line % 10 == 9:
			input()
