from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import auth,User
from . forms import RegisterForm
# Create your views here.


def home_page(request):
    return render(request,'recruitment/homepage.html')



def post(request):
    if request.user.is_superuser:
        return render(request,'recruitment/post.html')
    
    else:
        return redirect('/recruitment')

def apply_teaching(request):
    if request.user.is_authenticated:
        return render(request,'recruitment/teaching.html')
    else:
        return redirect('/recruitment/login')

def apply_non_teaching(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
           return redirect('/recruitment') 
        else:
            return render(request,'recruitment/non-teaching.html')
    else:
        return redirect('/recruitment/login')

def teaching(request):
    return render(request,'recruitment/teaching_posts.html')

def non_teaching(request):
    return render(request,'recruitment/non_teaching_posts.html')

def create(request):
    if request.user.is_superuser:
        return render(request,'recruitment/create.html')
    else:
        return redirect('/recruitment')


def login(request):
    if request.method=="POST":
        username=request.POST['username']
        password=request.POST['password']

        user = auth.authenticate(username=username,password=password)

        if user is not None:
            auth.login(request,user)
            return redirect('/recruitment')

        else:
            return redirect('/recruitment/login')


    else:
        return render(request,'recruitment/login.html')


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect('/recruitment/login')
    else:
        form = RegisterForm()
    return render(request, 'recruitment/register.html', {'form': form})


def logout(request):
    auth.logout(request)
    return redirect('/recruitment')
