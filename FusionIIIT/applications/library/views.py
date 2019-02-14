from django.shortcuts import render

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

def libraryModule(request):
        yo={}
        yo1={}
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
        viewstate = soup.find(id="__VIEWSTATE")['value']
        viewgen = soup.find(id="__VIEWSTATEGENERATOR")['value']
        eventvalid = soup.find(id="__EVENTVALIDATION")['value']
        
        Status = "Complete"
        memberid = "74"
        
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
                    i=0
                    
                    for tr in div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
                                temp ={str(i):{"assn":tr.contents[1].text,
                                        "book_name":tr.contents[3].text,
                                        "due_date":tr.contents[5].text,
                                        "issue_date":tr.contents[6].text}
                                        }
                                i=i+1 
                                yo.update(temp)      

            else :
                    print("No Records Found")           
        
       # print("")
       # print("Technically Unprocessed Items")
       # for div in soup.find_all("div",{'id':'print15'}):
       #     if div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
       #         for tr in div.find_all("tr",{'class':['GridItem', 'GridAltItem']}):
       #             print("")
       #          #   print("Accession No. :",tr.contents[1].text)
       #          #   print("Call No.      :",tr.contents[2].text)
       #          #   print("Title         :",tr.contents[3].text)
       #          #   print("Author(s)     :",tr.contents[4].text)
       #          #   print("Due Date      :",tr.contents[5].text)
       #          #   print("Issue Date    :",tr.contents[6].text)
       #          #   print("Item Category :",tr.contents[7].text)        
       #     else :
       #             print("No Records Found")

        url2 ="CircTotalFineUserWise.aspx?title=Over%20Due%20Details%20of%20MembersD"
        #r2 = requests.get(url1+url2)
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
            #print("")
            due = td.text
            #print("Total O.D.C in Rupees:",td.text)
        #print("")
       # print("Dues on non returned items (Technically Processed Items) :")     
        for div in soup2.find_all("div",{'id':'print16'}):
            if div.find_all("tr",{'class':['GridItem','GridAltItem']}):
                
                for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
                    temp = {str(j):{"assn": tr.contents[1].text,
                                    "due_date": tr.contents[2].text,
                                    "tdod": tr.contents[3].text,
                                    "tod": tr.contents[4].text}}                  
                   # print("")
                   # print("Accession No.  :", tr.contents[1].text)
                   # print("Due Date       :", tr.contents[2].text)
                   # print("Totalday*O.D.C :", tr.contents[3].text)
                   # print("Total O.D.C    :", tr.contents[4].text)
                    j=j+1
                    yo1.update(temp)    
            else:
                print("No Records Found")       

    #    print("")       
    #    print("Dues on non returned items (Technically Nonprocessed Items) :")      
    #    for div in soup2.find_all("div",{'id':'print18'}):
    #        if div.find_all("tr",{'class':['GridItem','GridAltItem']}): 
    #            for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):

    #            #    print("")   
    #            #    print("Accession No.  :", tr.contents[1].text)
    #            #    print("Call No.       :", tr.contents[2].text)
    #            #    print("Title          :", tr.contents[3].text)
    #            #    print("Author(s)      :", tr.contents[4].text)
    #            #    print("Due Date       :", tr.contents[5].text)
    #            #    print("Totalday*O.D.C :", tr.contents[6].text)
    #            #    print("Total O.D.C    :", tr.contents[7].text)  
    #        else :
    #            #    print("No Records Found")               

      #  print("")       
      #  print("Dues on already returned items (Technically Processed Items) :")     
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
                    yo1.update(temp)                
                  #  print("")   
                  #  print("Accession No.  :", tr.contents[1].text)
                  #  print("Due Date       :", tr.contents[2].text)
                  #  print("Return Date    :", tr.contents[3].text)
                  #  print("Totalday*O.D.C :", tr.contents[4].text)
                  #  print("Total O.D.C    :", tr.contents[5].text)
                  #  print("Cause          :", tr.contents[6].text)
            else :
                    print("No Records Found")                           

    #    print("")       
    #    print("Dues on already returned items (Technically Nonprocessed Items) :")      
    #    for div in soup2.find_all("div",{'id':'print22'}):
    #        if div.find_all("tr",{'class':['GridItem','GridAltItem']}): 
    #            for tr in div.find_all("tr",{'class':['GridItem','GridAltItem']}):
    #              #  print("")   
    #              #  print("Accession No.  :", tr.contents[1].text)
    #              #  print("Due Date       :", tr.contents[2].text)
    #              #  print("Return Date    :", tr.contents[3].text)
    #              #  print("Totalday*O.D.C :", tr.contents[4].text)
    #              #  print("Total O.D.C    :", tr.contents[5].text)
    #              #  print("Cause          :", tr.contents[5].text)
    #        else :
    #                # print("No Records Found")       


        context={"data1": yo, "due": due, "data2": yo1}
        print(request.user)
        return render(request, "libraryModule/libraryModule.html", context)
