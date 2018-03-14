from django.conf.urls import url

from . import views

app_name = 'finance'

urlpatterns = [

    url(r'^finance/', views.financeModule, name='financeModule'),

]
