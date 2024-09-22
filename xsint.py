from utils import *

options = [
	'Username',
	'Network',
	'Email',
	'IP',
	'Settings',
	'Exit'
	]

while True:
	m = menu(options)
	if m == 0: username()
	elif m == 1: network()
	elif m == 2: email()
	elif m == 4: settings()
	elif m == 5: exit(0)
	continue
