from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render

def homepage(request):
    tab =[
        {
        'id' : 1,
        'name' : 'Study table',
        'quantity' : 3888,
        'currentlyin': 'H4'
    },{
        'id' : 2,
        'name' : 'Study chair',
        'quantity' : 3888,
        'currentlyin': 'H4'
    },{
        'id' : 3,
        'name' : 'Hostel Carts',
        'quantity' : 3888,
        'currentlyin': 'H4'
    },{
        'id' : 4,
        'name' : 'Hostel Fans',
        'quantity' : 3888,
        'currentlyin': 'H4'
    },{
        'id' : 5,
        'name' : 'Hostel Tubelights',
        'quantity' : 3888,
        'currentlyin': 'H4'
    },{
        'id' : 6,
        'name' : 'Hostel office sofa set',
        'quantity' : 14,
        'currentlyin': 'H4'
    },{
        'id' : 7,
        'name' : 'T.V.',
        'quantity' : 20,
        'currentlyin': 'Administration Block'
    },{
        'id' : 8,
        'name' : 'Table Tennis',
        'quantity' : 4,
        'currentlyin': 'H4'
    },{
        'id' : 9,
        'name' : 'Water Purifiers',
        'quantity' : 84,
        'currentlyin': 'H4'
    },{
        'id' : 10,
        'name' : 'Electric Geyser',
        'quantity' : 252,
        'currentlyin': 'H4'
    }
    ]
    return render(request, "./ps2/home.html/",{'tab': tab})

def add(request):
    return render(request, "./ps2/form.html/",{})
    #return HttpResponse("<h1> START WORKING ON IT !!!</h1>")