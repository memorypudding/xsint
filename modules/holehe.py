from subprocess import getoutput
def holehe(e):
	out = getoutput(f"holehe {e} --only-used").split("\n")
	results = [i for i in out if "[+]" in i][:-2]
	if results:
		return results
	else:
		return ["\033[91mNo Results.\033[0m"]
