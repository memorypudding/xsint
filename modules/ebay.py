import requests

headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
}

def ebay(email):
	try:
		s = requests.Session()
		r = s.get("https://accounts.ebay.com/acctxs/user?clientapptype=19", allow_redirects=False, headers=headers)
		print(r)
		if r.status_code == 307: return "Captcha Hit."
		headers['Cookie'] = f"nonsession={s.cookies.get_dict()['nonsession']}"                                      # add nonsession cookie to headers
		srt = [line.split('f":"', 1)[-1].split('"', 1)[0] for line in r.text.split('\n') if 'initCsrf' in line][-1] # get needed srt token
		data = f"identifier={email}&srt={srt}&hbi=0&ru=&srcappid=&clientapptype=19&pageType="
		r = s.post("https://accounts.ebay.com/acctxs/init", headers=headers, data=data, allow_redirects=False)
		print(r)
		if r.status_code == 302: return "Limit Exceeded."
		r = requests.get(f"https://accounts.ebay.com{r.json()['ru']}", headers=headers)
		print(r)
		phonenumber = [line.split(";\"><b>", 1)[-1].split('*<', 1)[0] for line in r.text.split("\n") if "text-desc" in line][-1]
		print(phonenumber)
		return phonenumber
	except KeyError:
		return "No Account Connected."

# TODO
# fix this or get rid of it. 
# note: might be tough to fix but atleast try.
