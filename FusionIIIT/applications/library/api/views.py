from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from applications.globals.models import ExtraInfo
from html_text import *
import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse, HttpResponse
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_library_details(request):
    issue_details = {}
    due_details_non_returned = {}
    due_details_returned = {}
    due = 0
    library_home_url = "http://softgranth.iiitdmj.ac.in/webopac/"
    library_issue_details_url = "frmissuesofuser.aspx?title=Issue%20Details%20of%20The%20%20Members"
    # issue_request = requests.get(library_home_url+library_issue_details_url)
    home_request = requests.get(library_home_url)
    issue_request = requests.get(library_home_url + library_issue_details_url, cookies=home_request.cookies)
    soup_issue = BeautifulSoup(issue_request.content, "html5lib")
    # Hidden Values that are sent along with the form detailes
    viewstate = soup_issue.find(id="__VIEWSTATE")['value']
    viewgen = soup_issue.find(id="__VIEWSTATEGENERATOR")['value']
    eventvalid = soup_issue.find(id="__EVENTVALIDATION")['value']

    Status = "Complete"
    memberid = ExtraInfo.objects.get(user=request.user).id # Userid of the member who logged in

    # Form values that need to be sent to the server
    #All Issued books(Returned and Non-Returned will be fetched)
    formfields = {'__VIEWSTATE': viewstate,
                  "__VIEWSTATEGENERATOR": viewgen,
                  '__EVENTVALIDATION': eventvalid,
                  'ctl00$ContentPlaceHolder1$RadiobuttonList': Status,
                  'ctl00$ContentPlaceHolder1$txtuseridIOU': memberid,
                  'ctl00$ContentPlaceHolder1$btnSearch': 'Search'}

    # Requesting server with the member detailes and form values
    issue_result = requests.post(library_home_url + library_issue_details_url, cookies=home_request.cookies, data=formfields)

    # Extracting the result of the above request issue_result
    soup_issue = BeautifulSoup(issue_result.content, "html5lib")

    # Extracting the required detailes(Book name, ISBN number, Date of Isuue, Return date ..) from the resultant soup
    for div in soup_issue.find_all("div", {'id': 'print13'}):
        if div.find_all("tr", {'class': ['GridItem', 'GridAltItem']}):
            index = 0

            for table_row in div.find_all("tr", {'class': ['GridItem', 'GridAltItem']}):
                new_row = {str(index): {"assn": table_row.contents[1].text,
                                 "book_name": table_row.contents[3].text,
                                 "due_date": table_row.contents[5].text,
                                 "issue_date": table_row.contents[6].text}
                        }
                index = index + 1
                issue_details.update(new_row)

    # Url for checking the dues of the members
    library_due_details_url = "CircTotalFineUserWise.aspx?title=Over%20Due%20Details%20of%20MembersD"
    due_request = requests.get(library_home_url + library_due_details_url, cookies=home_request.cookies)
    soup_issue = BeautifulSoup(due_request.content, "html5lib")

    # Hidden Values that are sent along with the form detailes
    viewstate = soup_issue.find(id="__VIEWSTATE")['value']
    viewgen = soup_issue.find(id="__VIEWSTATEGENERATOR")['value']
    eventvalid = soup_issue.find(id="__EVENTVALIDATION")['value']

    # Form values that need to be sent to the server
    formfields = {'__VIEWSTATE': viewstate,
                  "__VIEWSTATEGENERATOR": viewgen,
                  '__EVENTVALIDATION': eventvalid,
                  'ctl00$ContentPlaceHolder1$txtuserid': memberid,
                  'ctl00$ContentPlaceHolder1$cmdcheck': 'Enter'}

    # Requesting server with the member detailes and form values

    due_result = requests.post(library_home_url + library_due_details_url, cookies=home_request.cookies, data=formfields)

    # Extracting the result of the above request due_result
    soup_due = BeautifulSoup(due_result.content, "html5lib")

    # Extracting the required detailes(Book name, Date issued, Date returned, no of days delayed, Due amount) 
    # from the resultant soup

    for total_due in soup_due.find_all("div", {'id': 'print13'}):
        due = total_due.text
    if not due.strip():
        due = str(0.00)
    for div in soup_due.find_all("div", {'id': 'print16'}):
        if div.find_all("tr", {'class': ['GridItem', 'GridAltItem']}):
            index = 0
            for table_row in div.find_all("tr", {'class': ['GridItem', 'GridAltItem']}):
                new_row = {str(index): {"assn": table_row.contents[1].text,
                                 "due_date": table_row.contents[2].text,
                                 "tdod": table_row.contents[3].text,
                                 "tod": table_row.contents[4].text}}
                index = index + 1
                due_details_non_returned.update(new_row)

    for div in soup_due.find_all("div", {'id': 'print21'}):
        if div.find_all("tr", {'class': ['GridItem', 'GridAltItem']}):
            index = 0
            for table_row in div.find_all("tr", {'class': ['GridItem', 'GridAltItem']}):
                new_row = {str(index): {"assn": table_row.contents[1].text,
                                 "due_date": table_row.contents[2].text,
                                 "return_date": table_row.contents[3].text,
                                 "tdod": table_row.contents[4].text,
                                 "tod": table_row.contents[5].text,
                                 "cause": table_row.contents[6].text}}
                index = index + 1
                due_details_returned.update(new_row)

    res= {"issue_details": issue_details, "due_details_non_returned": due_details_non_returned, "due_details_returned": due_details_returned, "due": due}
    return JsonResponse(res, safe=False)

     
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def book_search(request):
    book_results = ""
    library_home_url = "http://softgranth.iiitdmj.ac.in/webopac/"
    home_request = requests.get(library_home_url)
    # Parse the JSON payload from the request body
    data = json.loads(request.body)
    if data.get('nametype') == "bookname":
        bookname = data.get('bookname')
        authorname = ""
    else:   
        authorname = data.get('authorname')
        bookname = ""

    catalogue_search_url = "BasicSearch.aspx?title=Basic%20Catalogue%20Search"
    catalogue_search_result_url = "searchresult.aspx"
    catalogue_request = requests.get(library_home_url + catalogue_search_url, cookies=home_request.cookies)
    soupb = BeautifulSoup(catalogue_request.content, "html5lib")
    viewstate = soupb.find(id="__VIEWSTATE")['value']
    viewgen = soupb.find(id="__VIEWSTATEGENERATOR")['value']
    eventvalid = soupb.find(id="__EVENTVALIDATION")['value']
    prevpage = soupb.find(id="__PREVIOUSPAGE")['value']
    formfields = {}
    if bookname:
        formfields = {'__VIEWSTATE': viewstate,
                        "__VIEWSTATEGENERATOR": viewgen,
                        "__PREVIOUSPAGE": prevpage,
                        '__EVENTVALIDATION': eventvalid,
                        'ctl00$ContentPlaceHolder1$txtSearchText': bookname,
                        'ctl00$ContentPlaceHolder1$SelectPageSize': '100',
                        'ctl00$ContentPlaceHolder1$cmdSearch': 'Search'}

    if authorname:
        formfields = {'__VIEWSTATE': viewstate,
                        "__VIEWSTATEGENERATOR": viewgen,
                        "__PREVIOUSPAGE": prevpage,
                        '__EVENTVALIDATION': eventvalid,
                        'ctl00$ContentPlaceHolder1$txtSearchText': authorname,
                        'ctl00$ContentPlaceHolder1$lstSearchType': 'Author',
                        'ctl00$ContentPlaceHolder1$SelectPageSize': '100',
                        'ctl00$ContentPlaceHolder1$cmdSearch': 'Search'}

    catalogue_result = requests.post(library_home_url + catalogue_search_result_url, cookies=home_request.cookies, data=formfields)
    soup_catalogue = BeautifulSoup(catalogue_result.content, "html5lib")

    # To remove span items around searched keyword
    for match in soup_catalogue.findAll('span'):
        match.unwrap()
    text = html_text.extract_text(str(soup_catalogue))
    text = text.split("Central Library", 1)[1]
    if text == '\nNo Result Found.\nNew Search':
        book_results = "N"
    else:
        start = "Search Results"
        end = "Total Records"
        book_results = (text.split(start))[1].split(end)[0]
        book_results = book_results.replace("Copies Information Reserve Add Keyword(s) Add To Cart Content Author Info Book Info",
                                "\n")
        book_results = book_results.split("\n")

    return JsonResponse(book_results, safe=False)

