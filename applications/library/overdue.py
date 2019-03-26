import requests
from bs4 import BeautifulSoup

url1 = "http://172.27.20.250/webopac/"
url2 ="CircTotalFineUserWise.aspx?title=Over%20Due%20Details%20of%20MembersD"
#r2 = requests.get(url1+url2)
r1 = requests.get(url1)
r2 = requests.get(url1+url2,cookies=r1.cookies)
soup = BeautifulSoup(r2.content,"html5lib")
viewstate = soup.find(id="__VIEWSTATE")['value']
viewgen = soup.find(id="__VIEWSTATEGENERATOR")['value']
eventvalid = soup.find(id="__EVENTVALIDATION")['value']
formfields={'__VIEWSTATE':viewstate,
			"__VIEWSTATEGENERATOR":viewgen,
            '__EVENTVALIDATION':eventvalid,
            'ctl00$ContentPlaceHolder1$txtuserid':'74',
            'ctl00$ContentPlaceHolder1$cmdcheck': 'Enter'}
r3 = requests.post(url1+url2,cookies=r1.cookies,data=formfields) 
#print(r1.status_code)
#print(r2.status_code)
#print(r3.status_code)
 
soup2 = BeautifulSoup(r3.content,"html5lib")
for td in soup2.find_all("div", {'id':'print13'}):
		print("")
		print("Total O.D.C in Rupees:",td.text)
print("")		
print("Dues on non returned items (Technically Processed Items) :")		
for div in soup2.find_all("div",{'id':'print16'}):
	if div.find_all("tr",{'class':['GridItem','GridAltItem']}):	
		for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
			print("")	
			print("Accession No.  :", tr.contents[1].text)
			print("Due Date       :", tr.contents[2].text)
			print("Totalday*O.D.C :", tr.contents[3].text)
			print("Total O.D.C    :", tr.contents[4].text)
	else:
			print("No Records Found")		

print("")		
print("Dues on non returned items (Technically Nonprocessed Items) :")		
for div in soup2.find_all("div",{'id':'print18'}):
	if div.find_all("tr",{'class':['GridItem','GridAltItem']}):	
		for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
			print("")	
			print("Accession No.  :", tr.contents[1].text)
			print("Call No.       :", tr.contents[2].text)
			print("Title          :", tr.contents[3].text)
			print("Author(s)      :", tr.contents[4].text)
			print("Due Date       :", tr.contents[5].text)
			print("Totalday*O.D.C :", tr.contents[6].text)
			print("Total O.D.C    :", tr.contents[7].text)	
	else :
			print("No Records Found")				

print("")		
print("Dues on already returned items (Technically Processed Items) :")		
for div in soup2.find_all("div",{'id':'print21'}):
	if div.find_all("tr",{'class':['GridItem','GridAltItem']}):	
		for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
			print("")	
			print("Accession No.  :", tr.contents[1].text)
			print("Due Date       :", tr.contents[2].text)
			print("Return Date    :", tr.contents[3].text)
			print("Totalday*O.D.C :", tr.contents[4].text)
			print("Total O.D.C    :", tr.contents[5].text)
			print("Cause          :", tr.contents[5].text)
	else :
			print("No Records Found")							

print("")		
print("Dues on already returned items (Technically Nonprocessed Items) :")		
for div in soup2.find_all("div",{'id':'print22'}):
	if div.find_all("tr",{'class':['GridItem','GridAltItem']}):	
		for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
			print("")	
			print("Accession No.  :", tr.contents[1].text)
			print("Due Date       :", tr.contents[2].text)
			print("Return Date    :", tr.contents[3].text)
			print("Totalday*O.D.C :", tr.contents[4].text)
			print("Total O.D.C    :", tr.contents[5].text)
			print("Cause          :", tr.contents[5].text)
	else :
			print("No Records Found")					
