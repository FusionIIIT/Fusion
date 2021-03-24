from django.shortcuts import render


def hr2_index(request):
        """ Views for HR2 main page"""
        template='hr2Module/hr2_index.html'
        return render(request,template)


def hrAdmin(request):
        """ Views for HR2 Admin page """
        template='hr2Module/hradmin.html'
        return render(request,template)