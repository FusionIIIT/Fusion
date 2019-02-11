import requests
from bs4 import BeautifulSoup

url1 = "http://172.27.20.250/webopac/"
url2 ="frmissuesofuser.aspx?title=Issue%20Details%20of%20The%20%20Members"
#r2 = requests.get(url1+url2)
r1 = requests.get(url1)
r2 = requests.get(url1+url2,cookies=r1.cookies)
soup = BeautifulSoup(r2.content,"html5lib")
viewstate = soup.find(id="__VIEWSTATE")['value']
viewgen = soup.find(id="__VIEWSTATEGENERATOR")['value']
eventvalid = soup.find(id="__EVENTVALIDATION")['value']

Status = "Complete"
memberid = "2015181"

formfields={'__VIEWSTATE':viewstate,
			"__VIEWSTATEGENERATOR":viewgen,
            '__EVENTVALIDATION':eventvalid,
            'ctl00$ContentPlaceHolder1$RadiobuttonList': Status,
            'ctl00$ContentPlaceHolder1$txtuseridIOU': memberid,
            'ctl00$ContentPlaceHolder1$cmdcheck': 'Enter'}
r3 = requests.post(url1+url2,cookies=r1.cookies,data=formfields) 
#print(r1.status_code)
#print(r2.status_code)
#print(r3.status_code)
soup = BeautifulSoup(r3.content,"html5lib")
print("")
print("Technically Processed Items")
for div in soup.find_all("div",{'id':'print13'}):
	if div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
			for tr in div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
						print("")
						print("Accession No. :",tr.contents[1].text)
						print("Call No.      :",tr.contents[2].text)
						print("Title         :",tr.contents[3].text)
						print("Author(s)     :",tr.contents[4].text)
						print("Due Date      :",tr.contents[5].text)
						print("Issue Date    :",tr.contents[6].text)
						print("Item Category :",tr.contents[7].text)
	else :
			print("No Records Found")			

print("")
print("Technically Unprocessed Items")
for div in soup.find_all("div",{'id':'print15'}):
	if div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
		for tr in div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
			print("")
			print("Accession No. :",tr.contents[1].text)
			print("Call No.      :",tr.contents[2].text)
			print("Title         :",tr.contents[3].text)
			print("Author(s)     :",tr.contents[4].text)
			print("Due Date      :",tr.contents[5].text)
			print("Issue Date    :",tr.contents[6].text)
			print("Item Category :",tr.contents[7].text)		
	else :
			print("No Records Found")		
