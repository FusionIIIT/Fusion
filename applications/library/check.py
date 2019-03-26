import requests
from bs4 import BeautifulSoup

for x in range(0,255):
	str = "http://172.27.20." + x.__str__()
	r = requests.get(str)
	print(r.status_code,str)
	if(r.status_code == 200):
		print(str)
