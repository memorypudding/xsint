import cloudscraper

#patched, requires cf turnstile token
def hibp(email):
	try:
		s = cloudscraper.create_scraper()
		g = s.get(f"http://haveibeenpwned.com/unifiedsearch/{email}")
		i = g.json()['Breaches']
		breaches = [x['Name']for x in i]
		return breaches
	except Exception:
		return "None"
