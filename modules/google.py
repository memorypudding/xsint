import requests

def google(q):
	if "@" in q:
		url = f"https://mail.google.com/mail/gxlu?email={q}"
	else:
		url = f"https://mail.google.com/mail/gxlu?email={q}@gmail.com"
	return str(bool(requests.get(url).cookies))
