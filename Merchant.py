#!/usr/bin/env python3

import requests
import re
import time
import smtplib
import sys
import os
import json
from datetime import datetime
from notify_run import Notify
import platform

if platform.system() == 'Windows':
    CLEAR_STR = "cls" 
else:
    CLEAR_STR = "clear"


class Product:

	def __init__(self, name, link, cap):
		self.name = name
		self.link = link
		self.cap = cap
		self.avg = 0
		self.cycles = 0
	
	def to_dict(self):
		product = {	"name": self.name,
					"link": self.link,
					"cap": self.cap
					}	
		return product

	def update_avg(self, price):
		self.cycles += 1
		self.avg = (self.avg*(self.cycles-1) + price)/self.cycles 

	def __str__(self):
		prod_dict = self.to_dict()
		return  f"[{prod_dict['name']}]	 cap: {prod_dict['cap']}	 link: {prod_dict['link']}"


def log(string, time_mode="absolute"):
	string = str(string)
	if time_mode == "absolute":
		string = "[%s]: " + string
		now = datetime.now()
		ts = now.strftime("%H:%M:%S")
		print(string % ts)

	elif time_mode == "relative":
		string = "[%.2f]: " + string
		print(string % (time.time() - start_time))
	
	elif time_mode == "absolute|relative":
		string = "[ %s | %.2f ]: " + string
		now = datetime.now()
		ts = now.strftime("%H:%M:%S")
		print(string % (ts, (time.time() - start_time)))

	elif time_mode == "precise-absolute":
		string = "[%s]: " + string
		now = datetime.now()
		ts = now.strftime("%d/%m/%Y %H:%M:%S")
		print(string % ts)
	else:
		print(string)


def send_mail(product, price):

	link = product.link

	log(f'Sending mail to {recv_mail} ...')

	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.ehlo()
	server.starttls()
	server.ehlo()
	try:
		server.login(userbotmail,botpsw) 
	except smtplib.SMTPAuthenticationError:
		log("Failure in mailbot login")
		return
	
	subject = 'Price fell down!'
	body = f'Price for {product.name} is now at {price} ( price cap is setted as {product.cap})\n\nCheck the amazon link:\n{link}'

	msg = f"Subject: {subject}\n\n{body}"

	server.sendmail(userbotmail, recv_mail, msg)
	
	log('Email has been sent!')
	server.quit()
	#sys.exit() #exiting after mail sending

def send_notify(product, price):
	notify.send(f'Price for {product.name} is now at {price} ( price cap is setted as {product.cap})\n\nCheck the amazon link:\n{product.link}')
	log("Notified")



def deactive_prod(product, store=False):
	# removing product from list
	global product_list
	product_list.remove(product)
	if store:
		global stored_products
		stored_products.append(product)

def extract_site(link):
	site = link.split(".")[1]
	return site

def extract_title(r,title_match):
	 return  r.text[title_match.end():title_match.end()+200].split("\n\n\n\n\n\n")[1].replace("\n","")

def check_price(product_list):	
	global regex_compiled
	products = product_list.copy()
	for product in products:
		link = product.link
		cap = product.cap
		try:
			site = extract_site(link)
		except IndexError:
			print(f"[{product.name}] Wrong Link format")
			deactive_prod(product)
			continue

		log(f"[{product.name}]") 
		try:
			regexp_compiled, regext_compiled = regex_compiled[site]
		except KeyError:
				# first time saves compiled regex
				try:
					regexp, regext = regex[site]
					regexp_compiled = re.compile(regexp)
					regext_compiled = re.compile(regext)
					regex_compiled[site] = [regexp_compiled, regext_compiled]
				except KeyError:
					log("Scrape for site " + site + "not supported")
					print()
					continue

		log("Scraping...")
		r = requests.get(link, headers=headers)

		if r.status_code == 200:
		
			price_match = regexp_compiled.search(r.text)
			title_match = regext_compiled.search(r.text)

			log("Data successfully scraped")
			title = extract_title(r,title_match)
			log(title)
			
			price = r.text[price_match.end():price_match.end()+10].strip()
			price = price[2:].replace("\n","")
			price = price[:-3].replace(",",".")
			
			try: 
				price = float(price)
				product.update_avg(price)
				log(f"price: {price} €/$		[Average: {product.avg}]")
			except ValueError:
				log("Prouct not avaible (this may be caused to a failure in the scraping process, check online once to be sure)")
				print()
				continue	

			if price < cap:
				log(f'ALERT: Price under {cap} €/$')

				if email_flag:
					send_mail(product, price)
				if notify_flag:
					send_notify(product, price=price)

				deactive_prod(product, store=True)

			else:
				log(f'Setted Cap: {cap} €/$')
			print()
		else:
			log(f'Web Error for [{product.name}]: {link}\n')
			print()

def restore_credetials():
	try:
		global userbotmail, botpsw, recv_mail
		with open("botmail.conf", "r") as file:
			for line in file:
				if line.startswith("EMAIL"):
					line = line.split("=")[1]
					line.replace(" ","")
					userbotmail = line
				if line.startswith("TOKEN"):
					line = line.split("=")[1]
					line.replace(" ","")
					botpsw = line
				if line.startswith("RECIVER MAIL"):
					line = line.split("=")[1]
					line.replace(" ","")
					recv_mail = line
					
	except OSError:
		while True:
			if clear_flag:
				os.system(CLEAR_STR)
			print("\nFile botmail.conf not found, submit your credentials:")
			userbotmail = input("\nEMAIL: ").replace(" ","")
			botpsw = input("\nTOKEN: ").replace(" ","")
			recv_mail = input("\nRECIVER MAIL: ").replace(" ","")
			res = input("\n\nConfirm?	1/yes 	0/no\n\n")
			if res == "1" or res == "yes":
				try:
					with open("botmail.conf", "w") as file:
						file.write(f"EMAIL = {userbotmail}\n")
						file.write(f"TOKEN = {botpsw}\n")
						file.write(f"RECIVER MAIL = {recv_mail}\n")
				except OSError:
					print("\nERROR: Failure in writing in botmail.conf, credentials will not be saved\n")
				break
			elif res == "0" or res == "no":
				continue


def extract_products_from_json():
	product_list = []
	try: 
		with open(jsonfile,"r") as jfile:
			data = json.load(jfile)
			if not data:
				log("\nCannot restore products data from json file")
				exit()
			for prod in data:
				product_list.append(Product(prod["name"],prod["link"],prod["cap"]))
			return product_list

	except OSError:
		print()
		log("Failure in json file opening, creating one")
		return []
	except json.decoder.JSONDecodeError:
		print()
		log("Strange json format, ignoring saved products")
		return []
		

def store_products_in_json(product_list):
	try:
		with open(jsonfile, "w") as json_file:
			# Building Json data struct
			data = []
			for prod in product_list:
				data.append(prod.to_dict())
			json.dump(data, json_file, indent=4)
		log("Products file successfully updated")

	except OSError:
		log("Error in JSON opening, cannot save data")

def close(timesl=1):
    # close the program
    os.system(CLEAR_STR)
    print("\n\n\n           Bye         ,(è >è)/\n\n\n")
    time.sleep(timesl)
    os.system(CLEAR_STR)
    exit()

regex = {

	"amazon": ['a-size-medium a-color-price', 'a-size-large product-title-word-break' ]

}


regex_compiled = {}

headers = {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'Accept-Encoding': 'gzip, deflate, br',
	'Accept-Language': 'en-US,en;q=0.5',
	'Cache-Control': 'max-age=0',
	'Connection': 'keep-alive',
	'DNT': '1',
	'host': 'www.amazon.it',
	'referrer': 'https://www.google.com/',
	'TE': 'Trailers',
	'Upgrade-Insecure-Requests': '1',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
}

stored_products = []

jsonfile = "products.json"

# BOT MAIL credentials
# check for 2 step autentification, google app password and google unsecure app
userbotmail = ''
botpsw = ''
recv_mail = ''

start_time = time.time()
SLEEP_TIME = 300 	# seconds
TIMER =  6000 	# seconds

email_flag = False
notify_flag = False
clear_flag = False

if __name__ == "__main__":

	args = sys.argv

	try:	
		if "-clear" in args:
			clear_flag = True
		if "-email" in args:
			email_flag = True
			restore_credetials()
		if "-notify" in args:
			notify_flag = True
			notify = Notify()
		

		product_list = extract_products_from_json()

		while True:
			if clear_flag:
				os.system(CLEAR_STR)
			res = input("\nSet SLEEP TIME and TIMER?	1/yes	0/no\n\n")
			if res == "1" or res == "yes":
				while True:
					try:
						if clear_flag:
							os.system(CLEAR_STR)
						SLEEP_TIME = int(input("\nSLEEP TIME (secs): "))
						TIMER = int(input("\nTIMER (secs): "))
						break
					except ValueError:
						print("\nWrong format [e.g. SLEEP TIME (secs): 30, TIMER (secs): 6000]")
						input("\npress Enter to repeat")
						continue
				break
			elif res == "0" or res == "no":
				break


		while True:
			if clear_flag:
				os.system(CLEAR_STR)
			res = input("\nAdd a product?	1/yes	0/no\n\n")
			if res == "1" or res == "yes":
				try:
					if clear_flag:
						os.system(CLEAR_STR)
					name = input("\nName: ")
					cap = float(input("Cap (price under which notify): "))
					link = input("Link: ")
					product = Product(name, link, cap)
					product_list.append(product)
				except ValueError:
					print("\nWrong format [e.g. Cap: 23.45]")
					input("\npress Enter to repeat")
					continue
			elif res == "0" or res == "no":
				if clear_flag:
					os.system(CLEAR_STR)
				print()
				for product in product_list:
					print(product)
					print()
				input("\npress Enter to start Bot")
				break

	
		while True:		
			delta_time = (time.time() - start_time)
			if delta_time > TIMER:
				print("\n\n")
				log("TIME OUT!")
				input("\nPress Enter to exit")
				break
			if clear_flag:
				os.system(CLEAR_STR)
			log('##### Bot run starting ... Operating for %.2f secs [SLEEP TIME = %d | TIMER: %d  secs]' % (delta_time, SLEEP_TIME, TIMER))
			print()
			check_price(product_list)
			time.sleep(SLEEP_TIME) 
	except KeyboardInterrupt:
		pass
		
	store_products_in_json(product_list + stored_products)
	close()

