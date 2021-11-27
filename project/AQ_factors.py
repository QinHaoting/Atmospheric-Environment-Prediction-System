# !/usr/bin/env python
# coding=utf-8
"""
@File       : AQ_factors.py
@Time       ：2021/9/14 18:49
@Author     : Haoting Qin
@E-mail     : 1165101405@qq.com
"""
import re
import time

import pandas as pd
import pymysql
import requests
from bs4 import BeautifulSoup
from envs.Project.Lib import re
from pandas import DataFrame
from selenium import webdriver
from sqlalchemy.exc import IntegrityError


def get_date(url: str) -> list:
	"""
	获取城市日期

	参数：
		- url: 启动页地址

	返回：
		- dates: 年月列表
	"""
	# 伪装成浏览器代理
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
	}
	# 获取响应
	response = requests.get(url, headers=headers)
	dates = []
	try:
		print(response.status_code)
		if response.status_code == 200:  # 正常访问
			# 利用lxml进行解析
			soup = BeautifulSoup(response.text, 'lxml')
			# soup = BeautifulSoup(response.text, 'html.parser')  # 出错点！~已修改
			dates_ = soup.find_all('li')
			print(dates_)
			for i in dates_:
				if i.a:  # 去除空值
					li = i.a.text  # 提取li标签下的a标签
					li = li.strip()  # 去除空格
					date = re.findall('[0-9]*', li)  # ['2019', '', '12', '', '']
					year = date[0]
					month = date[2]
					if month and year:  # 去除不符合要求的内容
						date_new = ''.join([year, month])  # 合并成所需的20xxyy格式，如201401
						dates.append(date_new)
			dates.reverse()
			return dates
	except:
		print('日期获取失败！')


def spider(url: str) -> DataFrame:
	"""
	爬取数据
	由于网站加入了反爬机制，BeautifulSoup、Xpath均无法获取数据
	这里使用selenium

	参数:
		- url: 待爬取地址

	返回:
		- dataFrame: 某月份的AQ数据
	"""
	browser.get(url)
	dataFrame = pd.read_html(browser.page_source, header=0)[0]  # 返回第一个Dataframe
	time.sleep(1.5)  # 间歇时长，防止频繁访问
	if not dataFrame.empty:
		dataFrame.to_csv('AQ_data.csv', mode='a', index=False)  # 将数据存入csv文件中
		print(url + '数据爬取已完成')
		return dataFrame  # 返回Dataframe以写入数据库
	else:
		return spider(url)  # 防止网络还没加载出来就爬取下一个url


if __name__ == '__main__':
	base_url = 'http://www.tianqihoubao.com/aqi/'
	city_name = 'chongqing'  # 这里爬取重庆，注意不要用中文
	url = base_url + city_name + '-201401.html'  # 待爬取目标地址

	# 打开浏览器并初始化
	options = webdriver.ChromeOptions()
	options.add_argument("start-maximized")
	options.add_argument("--disable-blink-features=AutomationControlled")
	options.add_experimental_option("excludeSwitches", ["enable-automation"])
	options.add_experimental_option("useAutomationExtension", False)
	browser = webdriver.Chrome(options=options)
	browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
		'source': '''Object.defineProperty(navigator, 'webdriver', {
            get: () =>false'''
	})

	# 建立数据库连接
	conn = pymysql.connect(host='localhost', user='root', db='srtp_database', passwd='123456', charset='utf8')
	cursor = conn.cursor()  # 获取cursor游标

	# 获取日期列表
	start_index = 3  # 从201401开始爬取
	dates = get_date(url)[start_index:-1]

	list_data = []
	list_row = []

	# 逐个网页爬取
	for date in dates:
		url = base_url + city_name + '-' + date + '.html'  # 待爬取目标地址
		df = spider(url)

		time.sleep(1.5)  # 间歇访问

		for i in range(0, df.shape[0]):  # 行
			for j in range(df.shape[1]):  # 列
				data = df.iloc[i, j]
				list_row.append(data)
			list_data.append(list_row)
			list_row = []  # 清空当前行数据，为下一次添加做准备

	# 将数据逐条写入数据库
	for n in range(len(list_data)):
		sql = 'insert into aqidata (Date, Grade, AQI, PM2_5, PM10, SO2, NO2, CO, O3)' \
			  ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
		try:
			x = cursor.execute(sql, (list_data[n][0], list_data[n][1], float(list_data[n][2]),
									 float(list_data[n][3]), float(list_data[n][4]), float(list_data[n][5]),
									 float(list_data[n][6]), float(list_data[n][7]), float(list_data[n][8])))
		except IntegrityError:
			print('IntegrityError happened!')
		conn.commit()
	cursor.close()  # 关闭游标cursor
	conn.close()  # 关闭连接
	browser.close()  # 关闭浏览器
	print('所有数据爬取已完成！')
