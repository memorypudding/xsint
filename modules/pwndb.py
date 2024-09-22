from bs4 import BeautifulSoup
from lxml import etree
import requests

# site is gone

url = "https://pwndb2am4tzkvold.tor2web.io"
headers = {"Host": "pwndb2am4tzkvold.tor2web.io",
"Content-Type": "application/x-www-form-urlencoded"}

parse = lambda data: [line.strip().split("=>", 1)[-1].strip() for item in data for line in item.split('\n') if '[password] =>' in line]
        
def pwndb(email):
    email = email.split("@")
    data = f"luser={email[0]}&domain={email[-1]}&luseropr=0&domainopr=0&submitform=em"
    try:
        r = requests.post(url, data=data, headers=headers, timeout=10)
    except Exception:
        return f"request failed."
    if r.status_code != 200: return f"Request failed: {r.status_code}"
    soup = BeautifulSoup(r.text, 'html.parser')
    dom = etree.HTML(str(soup))
    print(dom.xpath('/html/body/div/section[4]/pre')[0].text)
    data = dom.xpath('/html/body/div/section[4]/pre')[0].text.split("Array")
    return parse(data[2:]) if len(data) != 2 else "No results found."
