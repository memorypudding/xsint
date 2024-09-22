from utils.settings import *
import requests

# patched by tumblr

headers = {"Content-Type": "application/json"}
proxies = {"http": "http://127.0.0.1:8080",
"https":"http://127.0.0.1:8080"}

def tumblr(email):
	# login data
	data = f'{{"password":"{get_setting("tumblr", "password")}","grant_type":"password","username":"{get_setting("tumblr", "email")}"}}'
	s = requests.Session()

	# get bearer token
	r = s.get("https://tumblr.com/login", proxies=proxies, verify=False)
	token = [l.split('EN":"', 1)[-1].split('"', 1)[0] for l in r.text.split("\n")  if 'API_TOKEN' in l][0]
	headers["Authorization"] = f"Bearer {token}"

	# login
	r = s.post("https://www.tumblr.com/api/v2/oauth2/token", headers=headers, data=data, proxies=proxies, verify=False)
	if r.status_code == 200:
		headers['X-Csrf'] = r.headers['X-Csrf']
		headers['Cookie'] = f"sid={r.cookies.get_dict()['sid']}"
		data = f'{{"email":"{email}"}}'
		# search the email
		r = s.post("https://www.tumblr.com/api/v2/user/follow", data=data, headers=headers, proxies=proxies, verify=False)
		if r.status_code == 200:
			blogurl = r.json()['response']['blog']['url']
			username = r.json()['response']['blog']['name']
			return {"blogurl": blogurl, "username": username}
		else:
			return "No User Found."
	else:
		return "Please add credentials in settings."

