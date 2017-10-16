from django.contrib.auth.decorators import login_required

# from django.http import HttpResponse
# from . forms import AddDropCourseForm

# Create your views here.


@login_required(login_url='/login')
def add_course(request):
    pass

def drop_course(request):
    pass
