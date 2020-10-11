import requests
import feedparser
import html2text
import re
import re as regex
from bs4 import BeautifulSoup          # For processing HTML
from bs4 import BeautifulStoneSoup     # For processing XML
import bs4   
import time  
from termcolor import colored, cprint
import sys
import colorama
import datefinder
import datetime
import pytz
import telegram
from money_parser import price_str
import numpy as np
import pandas as pd
import keyword
from nltk import word_tokenize

import requests
colorama.init()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

rss_url = ""

h = html2text.HTML2Text()
h.ignore_links = True

def preclean_input_text(text):
  cleaned_text = regex.sub(r'[a-z]:\s', ' ', text, flags=re.IGNORECASE)
  return cleaned_text
  
def parse_date_information(text):
  date_info = list(datefinder.find_dates(text.lower()))
  return date_info  


def extract_duedate(text):
    # Sanitize the text for datefinder by replacing the tricky parts 
    # with a non delimiter character
    text = re.sub(':|Rs[\d,\. ]+', '|', text, flags=re.IGNORECASE)

    return print(list(datefinder.find_dates(text))[-1])
	
def bot_sendtext(bot_message):
	
	### Send text message
	bot_token = ''
	bot_chatID = ''
	send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
 
	requests.get(send_text)	

job_buffer = []

# introduction 
fix_price_filter = input("Fixed price lower bound to filter vacancies (enter the number): ") 
lower_hour_price_filter = input("Lower price limit per hour to filter vacancies (enter the number): ") 
upper_hour_price_filter = input("Upper price limit per hour to filter vacancies (enter the number): ") 
key_word_filter = input("Enter the keyword: ") 

fix_price_filter = int(fix_price_filter)
lower_hour_price_filter = int(lower_hour_price_filter)
upper_hour_price_filter = int(upper_hour_price_filter)
key_word_filter = key_word_filter.lower()

while True:
	
	d = feedparser.parse(rss_url)
	
	for i in d.entries:
		# calculations
		
		# Title 
		title_message = h.handle(i['title'])[:-11]
		title_message = title_message.upper()
		
		# Money 
		soup = BeautifulSoup(''.join(h.handle(i['summary'])))
		r = r"(\$[0-9,.]+)"
		money = re.findall(r, soup.text)
		cleaned_string = preclean_input_text(soup.text)
		
		# Clean date
		try:	
			job_time_published = list(parse_date_information(cleaned_string))[-1] 
			job_time_published_date = job_time_published.date()
			job_time_published_time = job_time_published.time()
		except TypeError:
			job_time_published_date = datetime.datetime.now().date()
			job_time_published_time = datetime.datetime.now().time()
			
		# Greenwich time 
		tz = pytz.timezone('Etc/Greenwich')
		Greenwich_now = datetime.datetime.now(tz)
		
		# Current time 
		now = datetime.datetime.now()
		
		# Time Difference
		hours_to_minutes = job_time_published_time.hour * 60
		published_minutes = job_time_published_time.minute + hours_to_minutes
		greenwich_now_to_minutes = Greenwich_now.hour * 60
		greenwich_minutes = Greenwich_now.minute + greenwich_now_to_minutes
		delta = greenwich_minutes - published_minutes
		print("\n" * 5)
		
		#new_notification 
		if delta < 25:
			new_notification = "-------------------------------NEW-------------------------------"
			cprint(new_notification, 'green')
		else:
			pass
		
		print("Title")
		#print("--------------------------------------------------")
		cprint(title_message, 'red')
		#print("--------------------------------------------------")
		print("Description")
		#print("--------------------------------------------------")
		if len(money) == 2:
			money_2 = "{} - {}".format(money[0], money[1])
			cprint(money_2, 'green')
		if len(money) == 1:
			money_1 = "Fix price: {}".format(money[0])
			cprint(money_1, 'green')
		if len(money) == 0:
			cprint("Unknow money", 'red')
			
		#print("--------------------------------------------------")
		
		print("Time")
		
		#time 
		
		print(cleaned_string)
		
		# search keyword 
		tokens = word_tokenize(cleaned_string)
		tokens_title = word_tokenize(title_message)
	
		tokens.extend(tokens_title)
		tokens = [x.lower() for x in tokens]
		
		if key_word_filter in tokens:
			print("The word " + key_word_filter + " was found") 

		cprint(job_time_published_date, 'yellow')
		cprint(job_time_published_time, 'yellow')
		
		# telegram notification 
		# conditions 
		
		df = pd.read_csv("upwork_base.csv")
		
		if title_message not in job_buffer:
			job_buffer.append(title_message)
	
			if len(money) == 2:
				money_digit = float(price_str(money[1]))
				row_1 = {'date': job_time_published_date, 'time': job_time_published_time, 'title': title_message,
						'message': cleaned_string, 'fix_price': np.nan, 'price_min': money[0], 'price_max': money[1]}
				df = df.append(row_1, ignore_index=True)
				df.to_csv("upwork_base.csv", index=False)
				
				print(money_digit)
				if money_digit >= lower_hour_price_filter:
					bot_message = ("%s,  %s, %s, %s " % (title_message, money[0], money[1], cleaned_string))
					#bot_message = "{0}, {1}, {2}, {3}".fomrat(title_message, money[0], money[1], cleaned_string)	
					bot_sendtext(bot_message)
				
			if len(money) == 1:
				row_2 = {'date': job_time_published_date, 'time': job_time_published_time, 'title': title_message, 
						'message': cleaned_string, 'fix_price': money[0], 'price_min': np.nan, 'price_max': np.nan}
				df = df.append(row_2, ignore_index=True)
				df.to_csv("upwork_base.csv", index=False)

				money_digit = float(price_str(money[0]))
				if money_digit > fix_price_filter:
					bot_message = ("%s,  %s,  %s " % (title_message, money[0], cleaned_string))
					bot_sendtext(bot_message)
					
			if len(money) == 0:
				row_3 = {'date': job_time_published_date, 'time': job_time_published_time, 'title': title_message, 
						'message': cleaned_string, 'fix_price': np.nan, 'price_min': np.nan, 'price_max': np.nan}
				df = df.append(row_3, ignore_index=True)
				df.to_csv("upwork_base.csv", index=False)
					
			else:
				pass
		if title_message in job_buffer:
			pass 
			
		print("_______________________________________________________________")
		time.sleep(3)