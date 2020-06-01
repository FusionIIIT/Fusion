from django.shortcuts import render
from django.contrib.auth.decorators import login_required

buildings = [
    {
        'id': 'p',
        'name': 'Core Lab Complex',
        'status': 'incomplete',
        'date_approval': '30-12-05',
        'date_start': '30-12-05',
        'amount': 9999999
    },
    {
        'id': 'q',
        'name': 'LHTC',
        'status': 'incomplete',
        'date_approval': '15-11-05',
        'date_start': '05-12-05',
        'amount': 8960099
    },
    {
        'id': 'r',
        'name': 'Central Mess',
        'status': 'occupied',
        'date_approval': '21-06-06',
        'date_start': '13-11-06',
        'amount': 8899999
    },
    {
        'id': 's',
        'name': 'Hall 4',
        'status': 'complete',
        'date_approval': '22-08-07',
        'date_start': '12-10-08',
        'date_end': '24-07-08',
        'amount': 9085990
    }
]
projects = [
    {
        'name': 'Cricket Ground',
        'status': 'complete',
        'date_approval': '22-08-07',
        'date_start': '12-10-08',
        'date_end': '18-05-09',
        'amount': 9085999,
    },
    {
        'name': 'Boundary Wall',
        'status': 'incomplete',
        'date_approval': '22-08-07',
        'date_start': '12-10-08',
        'date_end': '18-05-09',
        'amount': 9085999,
    }
]

estate = [
    {
        'id': 1,
        'name': 'Core Lab Complex',
        'dateIssued': '30-12-05',
        'dateStarted': '30-12-05',
        'dateOccupied': '',
        'dateCompleted': '',
        'estimatedCost': 9999999,
        'actualCost': 9999999,
        'numRooms': 0,
        'numWashrooms': 0,
        'constructionTaskList': [],
        'maintenanceTaskList': [],
        'inventoryList': []
    },
    {
        'id': 2,
        'name': 'LHTC',
        'dateIssued': '15-11-05',
        'dateStarted': '15-11-05',
        'dateOccupied': '',
        'dateCompleted': '',
        'estimatedCost': 8960099,
        'actualCost': 0,
        'numRooms': 0,
        'numWashrooms': 0,
        'constructionTaskList': [],
        'maintenanceTaskList': [],
        'inventoryList': []
    },
    {
        'id': 3,
        'name': 'Central Mess',
        'dateIssued': '21-06-06',
        'dateStarted': '13-11-06',
        'dateOccupied': '',
        'dateCompleted': '',
        'estimatedCost': 8899999,
        'actualCost': 0,
        'numRooms': 0,
        'numWashrooms': 0,
        'constructionTaskList': [],
        'maintenanceTaskList': [],
        'inventoryList': []
    },
    {
        'id': 4,
        'name': 'Hall 4',
        'dateIssued': '22-08-07',
        'dateStarted': '12-10-08',
        'dateOccupied': '30-07-08',
        'dateCompleted': '24-07-08',
        'estimatedCost': 9085990,
        'actualCost': 0,
        'numRooms': 0,
        'numWashrooms': 0,
        'constructionTaskList': [],
        'maintenanceTaskList': [],
        'inventoryList': []
    }
]


@login_required(login_url='/accounts/login/')
def estate(request):

    context = {
        'buildings': buildings,
        'projects': projects
    }

    return render(request, "estate/home.html", context)
