import requests
import simplejson

headers = {
"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
'Host': 'www.paypal.com'
}

def paypal(email):
	s = requests.Session()
	r = s.get("https://www.paypal.com/authflow/password-recovery/", headers=headers)
	csrf = [line.split('f" value="', 1)[-1].split('"', 1)[0] for line in r.text.split('\n') if '_csrf' in line][0]
	anw = [line.split('sid" value="', 1)[-1].split('"', 1)[0] for line in r.text.split('\n') if 'anw_sid' in line][0]
	headers['Content-Type'] = "application/json"
	headers['Cookie'] = f"nsid={r.cookies.get_dict()['nsid']}"
	data = f'{{"email":"{email}","_csrf":"{csrf}","anw_sid":"{anw}"}}'
	r = s.post("https://www.paypal.com/authflow/password-recovery", headers=headers, data=data)
	print(r.text)
	try:
		i = r.json()['clientInstanceId']
		r = s.get(f"https://paypal.com/authflow/entry/?clientInstanceId={i}&anw_sid={anw}", headers=headers)
		return r.text
	except simplejson.errors.JSONDecodeError:
		print("Captcha Hit.")
		pass
# TODO
# FIX THIS SHIT
