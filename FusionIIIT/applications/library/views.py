from django.shortcuts import render
from applications.globals.models import ExtraInfo
from django.views.decorators.csrf import csrf_exempt
import html_text
from django.utils.functional import cached_property




   #   """
   #   This Function is used to View the Issued Items of the user acording to the tags.
   #   The Data is scraped from the institutes library module hosted on the web OPAC server.
   #    We are using BeautifulSoup library to scrape the data from the web .
   #    (refer to Beautifulsoup Documentation)
   #    The parsed web page can be accessed using beautiful soup.
   # @variables:
   #       context-holds data to make necessary changes in the template
   #       r1-url1 = "http://172.27.20.250/webopac/"
   #       r2-requests.get(url1+url2,cookies=r1.cookies)
   #       r3-for cookies as requests (using beautiful soup with cookies)
   #       status- status of the issued items
   #       memberid-of the current user
   # @param:
   #       requests-
   #
   #
   #   """
@csrf_exempt

def libraryModule(request):
        issue_details={}
        due_details1={}
        due_details2={}
        textb=""
        due=0
        j=0
        import requests
        from bs4 import BeautifulSoup
        url1 = "http://172.27.20.250/webopac/"
        url2 ="frmissuesofuser.aspx?title=Issue%20Details%20of%20The%20%20Members"
        #r2 = requests.get(url1+url2)
        r1 = requests.get(url1)
        r2 = requests.get(url1+url2,cookies=r1.cookies)
        soup = BeautifulSoup(r2.content,"html5lib")
# Hidden Values that are sent along with the form detailes
        viewstate = soup.find(id="__VIEWSTATE")['value']
        viewgen = soup.find(id="__VIEWSTATEGENERATOR")['value']
        eventvalid = soup.find(id="__EVENTVALIDATION")['value']

        Status = "Complete"
        memberid = ExtraInfo.objects.get(user=request.user).id   #Userid of the member who logged in

#Form values that need to be sent to the server
        formfields={'__VIEWSTATE':viewstate,
                    "__VIEWSTATEGENERATOR":viewgen,
                    '__EVENTVALIDATION':eventvalid,
                    'ctl00$ContentPlaceHolder1$RadiobuttonList': Status,
                    'ctl00$ContentPlaceHolder1$txtuseridIOU': memberid,
                    'ctl00$ContentPlaceHolder1$cmdcheck': 'Enter'}

#Requesting server with the member detailes and form values
        r3 = requests.post(url1+url2,cookies=r1.cookies,data=formfields)

#Extracting the result of the above request r3
        soup = BeautifulSoup(r3.content,"html5lib")
        print("")
        print("Technically Processed Items")


# Extracting the required detailes(Book name, ISBN number, Date of Isuue, Return date ..) from the resultant soup
        for div in soup.find_all("div",{'id':'print13'}):
            if div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
                    i=0

                    for tr in div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
                                temp ={str(i):{"assn":tr.contents[1].text,
                                        "book_name":tr.contents[3].text,
                                        "due_date":tr.contents[5].text,
                                        "issue_date":tr.contents[6].text}
                                        }
                                i=i+1
                                issue_details.update(temp)

            else :
                    print("No Records Found")

# Url for checking the dues of the members
        url2 ="CircTotalFineUserWise.aspx?title=Over%20Due%20Details%20of%20MembersD"
        r2 = requests.get(url1+url2,cookies=r1.cookies)
        soup = BeautifulSoup(r2.content,"html5lib")

# Hidden Values that are sent along with the form detailes
        viewstate = soup.find(id="__VIEWSTATE")['value']
        viewgen = soup.find(id="__VIEWSTATEGENERATOR")['value']
        eventvalid = soup.find(id="__EVENTVALIDATION")['value']

#Form values that need to be sent to the server
        formfields={'__VIEWSTATE':viewstate,
                     "__VIEWSTATEGENERATOR":viewgen,
                     '__EVENTVALIDATION':eventvalid,
                     'ctl00$ContentPlaceHolder1$txtuserid':memberid,
                     'ctl00$ContentPlaceHolder1$cmdcheck': 'Enter'}

#Requesting server with the member detailes and form values

        r3 = requests.post(url1+url2,cookies=r1.cookies,data=formfields)

#Extracting the result of the above request r3
        soup2 = BeautifulSoup(r3.content,"html5lib")

#Extracting the required detailes(Book name, Date issued, Date returned, no of days delayed, Due amount) from the resultant soup
        for td in soup2.find_all("div", {'id':'print13'}):

            due = td.text
        for div in soup2.find_all("div",{'id':'print16'}):
            if div.find_all("tr",{'class':['GridItem','GridAltItem']}):
                for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
                    temp = {str(j):{"assn": tr.contents[1].text,
                                    "due_date": tr.contents[2].text,
                                    "tdod": tr.contents[3].text,
                                    "tod": tr.contents[4].text}}
                    j=j+1
                    due_details1.update(temp)
            else:
                print("No Records Found")

        for div in soup2.find_all("div",{'id':'print21'}):
            if div.find_all("tr",{'class':['GridItem','GridAltItem']}):
                for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
                    temp = {str(j):{"assn": tr.contents[1].text,
                                    "due_date": tr.contents[2].text,
                                    "return_date": tr.contents[3].text,
                                    "tdod": tr.contents[4].text,
                                    "tod": tr.contents[5].text,
                                    "cause": tr.contents[6].text}}
                    j=j+1
                    due_details2.update(temp)

            else :
                    print("No Records Found")




# Book search
        if request.method == 'POST':
            if request.POST.get('nametype') == "bookname":
                bookname = request.POST['bookname']
                authorname=""
            else:
                authorname = request.POST['authorname']
                bookname=""

            url3 ="BasicSearch.aspx?title=Basic%20Catalogue%20Search"
            url4="searchresult.aspx"
            rb1 = requests.get(url1)
            rb2 = requests.get(url1+url3,cookies=r1.cookies)
            soupb = BeautifulSoup(rb2.content,"html5lib")
            viewstate = soupb.find(id="__VIEWSTATE")['value']
            viewgen = soupb.find(id="__VIEWSTATEGENERATOR")['value']
            eventvalid = soupb.find(id="__EVENTVALIDATION")['value']
            prevpage = soupb.find(id="__PREVIOUSPAGE")['value']
            if bookname:
                formfields={'__VIEWSTATE':viewstate,
                            "__VIEWSTATEGENERATOR":viewgen,
                            "__PREVIOUSPAGE":prevpage,
                            '__EVENTVALIDATION':eventvalid,
                            'ctl00$ContentPlaceHolder1$txtSearchText':bookname,
                            'ctl00$ContentPlaceHolder1$SelectPageSize':'100',
                            'ctl00$ContentPlaceHolder1$cmdSearch': 'Search'}

            if authorname:
                formfields={'__VIEWSTATE':viewstate,
                            "__VIEWSTATEGENERATOR":viewgen,
                            "__PREVIOUSPAGE":prevpage,
                            '__EVENTVALIDATION':eventvalid,
                            'ctl00$ContentPlaceHolder1$txtSearchText':authorname,
                            'ctl00$ContentPlaceHolder1$lstSearchType':'Author',
                            'ctl00$ContentPlaceHolder1$SelectPageSize':'100',
                            'ctl00$ContentPlaceHolder1$cmdSearch': 'Search'}
            rb3 = requests.post(url1+url4,cookies=r1.cookies,data=formfields)
            soupb2 = BeautifulSoup(rb3.content,"html5lib")
            #textb=soupb2.get_text()
            text = html_text.extract_text(str(soupb2))
            text=text.split("Central Library",1)[1]
            if text=='\nNo Result Found.\nNew Search':
                textb = "N"
            else:
                start = "Search Results"
                end = "Total Records"
                textb = (text.split(start))[1].split(end)[0]
                textb=textb.replace("Copies Information Reserve Add Keyword(s) Add To Cart Content Author Info Book Info","\n")
                textb=textb.split("\n")






        context={"data1": issue_details, "due": due, "data2": due_details1,"data3":due_details2,"bookresults":textb}
        print(request.user)
        return render(request, "libraryModule/libraryModule.html", context)
