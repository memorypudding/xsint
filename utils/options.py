# module imports
from terminaltables import SingleTable
from pwinput import pwinput
from tqdm import tqdm
import time

# file imports
from utils import *
from modules import *

display = lambda results: [print(i) for i in sorted(results, key=len)[::-1]]
dicttodata = lambda d: [[k, d[k]]for k in d.keys()]
listtodata = lambda l: [[i]for i in l]
results = []

def result(data, title, r=False):
	t = type(data)
	if t == list:   t = SingleTable(listtodata(data), title=title)
	elif t == dict: t = SingleTable(dicttodata(data), title=title)
	elif t == str:  t = SingleTable([[data]], title=title)
	if r:           t = SingleTable(data, title=title)

	t.inner_heading_row_border = False
	results.append(t.table)
	
def load(module_list, q):
	pbarn = 100 / len(module_list)
	pbar = tqdm(total=100)
	for f in module_list:
		result(f(q), str(f).split(" ")[1])
		pbar.update(pbarn)
	pbar.close()
	clear()
	display(results) # this is to organize the output of all the results
	input("Press enter to return")
	results.clear()

def email():
	e = input("Email: ")

	module_list = [
		google,
		apple,
		#hibp,
		gravatar,
		#pwndb,
		#tumblr,
		twitter,
		holehe
	]
	load(module_list, e)

def username():
	u = input("Username: ")

	module_list = [
		twitter,
		google
	]
	load(module_list, u)

# TODO: finish wigle module
def network():
	i = input("SSID/BSSID: ")
	load([wigle], i)

# TODO: finish this/add modules
def ip():
	ip = input("IP: ")
	module_list = {
	}

# TODO: clean up settings function
def settings():
	while True:
		slist = [
			'Menu Colors',
			'Credentials',
			'Back'
		]
		m = menu(slist, "Settings")
		# Menu Colors
		if m == 0:
			while True:
				slist = [
					'Cursor Color',
					'Highlist Color',
					'Back'
				]
				m = menu(slist, "Settings")
				# Cursor Color
				if m == 0:
					while True:
						ccursor = get_setting('menu', 'cursorstyle')
						m = menu(colorlist, title=f"Current Cursor Color: {ccursor}")
						newcolor = colorlist[m]
						if newcolor != "Back": update_setting("menu", 'cursorstyle', newcolor)
						else: break
				# Option Highlight Color 
				elif m == 1:
					while True:
						chighlight = get_setting('menu', 'highlight')
						m = menu(colorlist, title=f"Current Hightlight Color: {chighlight}")
						newcolor = colorlist[m]
						if newcolor != "Back": update_setting("menu", 'highlight', newcolor)
						else: break
				elif m == 2: break
				continue
		elif m == 1:
			while True:
				s = readsettings()
				s.pop('menu')
				creds = list(s.keys())
				creds.append('Back')
				# shows modules
				m = menu(creds, "Credentials")
				if creds[m] == "Back": break
				else:
					while True:
						# shows actual credential types like email
						options = list(s[creds[m]].keys())
						options.append("Back")
						o = menu(options, creds[m])
						if options[o] == "Back": break
						else:
							c = pwinput(f"{options[o]}: ")
							update_setting(creds[m], options[o], c)
							print("Setting Updated!")
							time.sleep(2)
							continue


		elif m == 2: break
		continue
