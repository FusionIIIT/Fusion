from django.shortcuts import render
from django.contrib.auth.decorators import login_required

buildings = [
    {
        'id': 'p',
        'name': 'Core Lab Complex',
        'status': 'incomplete',
        'date_approval': '30-12-05',
        'date_start': '30-12-05',
        'amount': '9999999'
    },
    {
        'id': 'q',
        'name': 'LHTC',
        'status': 'incomplete',
        'date_approval': '15-11-05',
        'date_start': '05-12-05',
        'amount': '8960099'
    },
    {
        'id': 'r',
        'name': 'Central Mess',
        'status': 'occupied',
        'date_approval': '21-06-06',
        'date_start': '13-11-06',
        'amount': '8899999'
    },
    {
        'id': 's',
        'name': 'Hall 4',
        'status': 'complete',
        'date_approval': '22-08-07',
        'date_start': '12-10-08',
        'date_end': '24-07-08',
        'amount': '9085990'
    }
]


@login_required(login_url='/accounts/login/')
def estate(request):

    context = {
        'buildings': buildings
    }

    return render(request, "estate/home.html", context)
