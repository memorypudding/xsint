import json

sname = "settings.json"

try: open(sname)
except Exception: print("settings file not found...")

def readsettings():
	sfile = open(sname, 'r')
	settings = json.load(sfile)
	sfile.close()
	return settings

def writesettings(settings):
	sfile = open(sname, 'w')
	sfile.write(f"{settings}\n")
	sfile.close()

def update_setting(service, key, value):
	settings = readsettings()
	settings[service][key] = value
	writesettings(json.dumps(settings, indent=4))

def get_setting(service, key): 
	return readsettings()[service][key]

# example
# update_setting("tumblr", "email", "test@example.com")
# get_setting("tumblr", "email")
# returns test@example.com
