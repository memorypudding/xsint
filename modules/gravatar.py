import requests
import hashlib

def gravatar(email):
	try:
		hash = hashlib.md5(email.encode()).hexdigest()
		r = requests.get(f"https://gravatar.com/{hash}.json")
		info = r.json()['entry'][0]
		purl = info['profileUrl']
		username = info['preferredUsername']
		return {'username': username, 'url': purl}
	except TypeError:
		return "No account found."
