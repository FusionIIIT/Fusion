from django.conf.urls import url

from .views import compounder_view, healthcenter, student_view

app_name = 'healthcenter'

urlpatterns = [

    url(r'^$', healthcenter, name='healthcenter'),
    url(r'^compounder/$', compounder_view, name='compounder_view'),
    url(r'^student/$', student_view, name='student_view'),
]
