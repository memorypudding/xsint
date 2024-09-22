from subprocess import getoutput

ghunt = lambda email: print(getoutput(f"python3 GHunt/ghunt.py email {email}"))
