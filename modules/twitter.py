import requests

def getinfo(text: list):
	for line in text:
		if "We couldn't find your account" in line: return "No Account Not Found."
		elif "You've exceeded the number of attempts" in line: return "Rate Limited"
		elif "Enter your" and "to continue" in line: return "No Info"
	info = [line.split(">", 1)[-1].split("<")[0] for line in text if "<strong dir=" in line]
	# this checks if theres a phone num then adds to it
	if len(info) == 2: info[0] = f"(•••) •••-••{info[0]}"
	return info


def twitter(query):
	s = requests.Session()
	r = s.get("https://twitter.com/account/begin_password_reset?lang=en")
	authtoken = [line.split("e=\"")[-1].split('"')[0] for line in r.text.split('\n') if 'authenticity_token' in line][-1]
	data = f"authenticity_token={authtoken}&account_identifier={query}"
	headers = {"Cookie": f"_twitter_sess={r.cookies.get_dict()['_twitter_sess']}", "Content-Type": "application/x-www-form-urlencoded"}
	resreq = s.post("https://twitter.com/account/begin_password_reset?lang=en", headers=headers, data=data)
	info = getinfo(resreq.text.split("\n"))
	return info
