from django.shortcuts import render

# Create your views here.

def hr2_index(request):
    template = 'hr2Module/hr2_index.html'
    return render(request,template)
def hrAdmin(request):
    template = 'hr2Module/hradmin.html'
    return render(request,template)