from django.shortcuts import render

# Create your views here.

def hr2_index(request):
    template = 'hr2Module/hr2_index.html'
    return render(request,template)