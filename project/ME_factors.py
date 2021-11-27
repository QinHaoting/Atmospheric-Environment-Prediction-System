# !/usr/bin/env python
# coding=utf-8
"""
@File       : ME_factors.py
@Time       ：2021/10/11 20:36
@Author     : Haoting Qin
@E-mail     : 1165101405@qq.com
"""
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from envs.Project.Lib import re
from selenium import webdriver


def get_date(url: str) -> list:
	"""
	从url中获取日期信息

	参数：
		- url: 目标url

	返回：
		- dates: 日期数组
	"""
	headers = {  # 伪装成Chrome浏览器代理
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
	}
	# 获取响应
	response = requests.get(url, headers=headers)
	# 爬取的日期数组
	dates = []
	try:
		print(response.status_code)
		if response.status_code == 200:  # 正常访问
			# 利用lxml对网站内容进行解析
			soup = BeautifulSoup(response.text, 'lxml')
			dates_ = soup.find_all('option')
			for i in dates_:
				if i.text:  # 去除空值
					option = i.text  # 提取<option>标签下的内容
					option = option.strip()  # 去除空格
					# 利用正则表达式筛选出所需的日期信息
					date = re.findall('[0-9]*', option)
					# date格式为['2019', '', '12', '', '']，可见“年”在下标0，“月”在下标1
					year = date[0]
					month = date[2]
					if month and year:  # 去除不符合要求的内容
						date_new = ''.join([year, month])  # 合并成所需的20xxyy格式，如201401
						dates.append(date_new)
				else:
					pass
			dates.reverse()
			return dates
	except:
		print('日期获取失败！')


def spider(url):
	"""
	爬取数据
	由于网站加入了反爬机制，BeautifulSoup、Xpath均无法获取数据
	这里使用selenium
	"""
	headers = {  # 伪装成Chrome浏览器代理
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
	}
	# 获取响应
	response = requests.get(url, headers=headers)
	# 解析网页
	bs = BeautifulSoup(response.text, 'lxml')
	# 由于该网页的数据没有用标准的表格装填，故需找到相应的标签依次提取
	# 找到数据表并依次提取
	date_list = []
	week_list = []
	max_temp_list = []
	min_temp_list = []
	weather_list = []
	wind_list = []
	table = bs.find_all(class_='thrui')
	# 日期标签
	date_tag = re.compile('class="th200">(.*?)</')
	# 数据标签
	data_tag = re.compile('class="th140">(.*?)</')
	# 从表格中提取出所有日期项
	days = re.findall(date_tag, str(table))
	for day in days:
		# 日期标签的value为："2019-06-01 星期六 "
		# 故日期为
		date_length = len("2014-01-01")
		date_list.append(day[:date_length])
		# 对应的星期x为，记得去除空白@2
		week_list.append(day[date_length:].strip())
	# 从表格中提取出所有气象数据
	ME_data_days = re.findall(data_tag, str(table))

	for i in range(len(days)):
		# 一天有4个气象数据项，如'10℃', '4℃', '多云', '微风 小于3级'
		#                对应为最高温，最低温，天气，风向+风级
		max_temp_list.append(ME_data_days[i * 4 + 0])
		min_temp_list.append(ME_data_days[i * 4 + 1])
		weather_list.append(ME_data_days[i * 4 + 2])
		wind_list.append(ME_data_days[i * 4 + 3])
	dataFrame = pd.DataFrame({'日期': date_list,
							  '星期': week_list,
							  '最高温度': max_temp_list,
							  '最低温度': min_temp_list,
							  '天气': weather_list,
							  '风向风力': wind_list})
	# print(dataFrame)
	time.sleep(1.5)  # 间歇时长，防止频繁访问
	if not dataFrame.empty:
		dataFrame.to_csv('data/ME/ME_data.csv', mode='a', index=False)  # 将数据存入csv文件中
		print(url + '数据爬取已完成')
		return dataFrame  # 返回Dataframe以写入数据库
	else:
		return spider(url)  # 防止网络还没加载出来就爬取下一个url


if __name__ == '__main__':
	base_url = 'http://lishi.tianqi.com/'
	city_name = 'chongqing'  # 这里爬取重庆，注意不要用中文
	url = base_url + city_name + '/201401.html'  # 待爬取目标地址

	# 打开浏览器并初始化
	# options = webdriver.ChromeOptions()
	# options.add_argument("start-maximized")
	# options.add_argument("--disable-blink-features=AutomationControlled")
	# options.add_experimental_option("excludeSwitches", ["enable-automation"])
	# options.add_experimental_option("useAutomationExtension", False)
	# browser = webdriver.Chrome(options=options)
	# browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
	# 	'source': '''Object.defineProperty(navigator, 'webdriver', {
    #         get: () =>false'''
	# })

	# # 建立数据库连接
	# conn = pymysql.connect(host='localhost', user='root', db='srtp_database', passwd='123456', charset='utf8')
	# cursor = conn.cursor()     # 获取cursor游标
	#
	# 爬取日期列表
	start_index = (2014 - 2011) * 12  # 从201401开始爬取
	dates = get_date(url)[start_index:]
	print(dates)
	# dates = get_date(url)[3:-1]

	list_data = []
	list_row = []
	#
	for date in dates:
		url = base_url + city_name + '/' + date + '.html'  # 待爬取目标地址
		df = spider(url)
		# print(df)

		time.sleep(1.5)  # 间歇访问

		# for i in range(0, df.shape[0]):   # 行
		#     for j in range(df.shape[1]):  # 列
		#         data = df.iloc[i, j]
		#         list_row.append(data)
		#     list_data.append(list_row)
		#     list_row = []                # 清空

	# for n in range(len(list_data)):
	#     sql = 'insert into aqidata (Date , Grade, AQI, PM2_5, PM10, SO2, NO2, CO, O3)' \
	#           ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
	#     try:
	#         x = cursor.execute(sql, (list_data[n][0],        list_data[n][1],  float(list_data[n][2]),
	#                            float(list_data[n][3]), float(list_data[n][4]), float(list_data[n][5]),
	#                            float(list_data[n][6]), float(list_data[n][7]), float(list_data[n][8])))
	#     except IntegrityError:
	#         print('IntegrityError happened!')
	#     conn.commit()
	# cursor.close()  # 关闭cursor
	# conn.close()  # 关闭连接

	# browser.close()  # 关闭浏览器
	print('所有数据爬取已完成！')
