# Merchant
Merchant is a bot that chekcs discounts on your favorite products



## Flags

Cleaning bash:
	
	$ python3 Merchant.py -clear
		
	
Send emails if price is fell under CAP:
	
		$ python3 Merchant.py -email
		
		
Notify on smartphone if price is fell under CAP: 
		
		$ python3 Merchant.py -notify


## Requirements

1. Python3 
	
	https://www.python.org/downloads/
	https://docs.python-guide.org/starting/install3/linux/
	

2. Imports:

	a. Web scraping module

		import requests		
		
	b. Regex module
	
		import re	
		
	c. Time modules
		
		import time, datetime
		
	d. SMTP (emails) [Read Alert]
		
		import smtplib
		
	e. System modules
	   	
		import sys, os, platform
	   
	f. Manage Json files
		
		import json
	
	g. Telephone notifier [Read Alert]
		
		import notify
		
		
		
	
	

## ALERT:


To use Email options you have to set your bot email and token, check this sites:

https://support.google.com/accounts/answer/6010255?hl=en

https://stackabuse.com/how-to-send-emails-with-gmail-using-python/



To use Notify you have firstly to register your telephone

	$ notify-run register

Then scan the QR code with the target telephone





