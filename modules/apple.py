from json import loads
import json
import requests

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"}

def apple(email):
	try:
		s = requests.Session()
		r = s.get("https://iforgot.apple.com/password/verify/appleid", headers=headers)
		headers['Sstt'] = [loads(line)["sstt"] for line in r.text.split("\n") if "sstt" in line][0]
		headers['Content-Type'] = "application/json"
		data = f'{{"id":"{email}"}}'
		r = s.post("https://iforgot.apple.com/password/verify/appleid", data=data, headers=headers, allow_redirects=False).headers['Location']
		headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
		r = s.get(f"https://iforgot.apple.com{r}", headers=headers, allow_redirects=False).json()['trustedPhones'][0]
		c = r['countryCode']
		n = r['numberWithDialCode']
		return {"\033[32mCountry\033[0m": c, "\033[32mNumber\033[0m": n}
	except KeyError:
		ret = "No Account"
	except IndexError:
		ret = "Rate Limited"
	except json.decoder.JSONDecodeError:
		ret = "Request Failed"
	return ["\033[91m" + ret + "\033[0m"]

#TODO
# recode/add better error checking
