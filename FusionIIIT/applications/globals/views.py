from django.shortcuts import render


def index(request):
    context = {}

    return render(request, "globals/index1.html", context)


def about(request):

    teams = {
        'uiTeam': {
            'teamId': "uiTeam",
            'teamName': "Frontend Team",
        },

        'qaTeam': {
            'teamId': "qaTeam",
            'teamName': "Quality Analysis Team",
        },

        'eisTeam': {
            'teamId': "eisTeam",
            'teamName': "EIS Module Team",
        },

        'leaveTeam': {
            'teamId': "leaveTeam",
            'teamName': "Leave Module Team",
        },
    }

    context = {'teams': teams,
               'psgTeam': {
                   'dev1': {'devName': 'Anuraag Singh',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'Head UI Developer'
                            },

                   'dev3': {'devName': 'M. Arshad Siddiqui',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Database Designer'
                            },

                   'dev4': {'devName': 'Pranjul Mishra',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev5': {'devName': 'Saket Patel',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Head Developer'
                            },
               },

               'uiTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'Head UI Developer'
                            },

                   'dev2': {'devName': 'Mayank Saurabh',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI Developer'
                            },

                   'dev3': {'devName': 'Ravuri Abhignya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI Developer'
                            },
               },

               'qaTeam': {
                   'dev1': {'devName': 'Anuj Upadhaya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Member'
                            },

                   'dev2': {'devName': 'Avinash Kumar',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Head'
                            },

                   'dev3': {'devName': 'G. Vijay Ram',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Member'
                            },
               },

               'eisTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Mayank Saurabh',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI Developer'
                            },

                   'dev3': {'devName': 'M. Arshad Siddiqui',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Backend Developer'
                            },
               },

               'leaveTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Saket Patel',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Backend Developer'
                            },
               },
               }
    return render(request, "globals/about.html", context)


def login(request):
    context = {}

    return render(request, "globals/login.html", context)


def dashboard(request):
    context = {}

    return render(request, "dashboard/dashboard.html", context)
