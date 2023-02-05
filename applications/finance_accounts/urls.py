from django.conf.urls import url

from . import views

app_name = 'finance'

urlpatterns = [

    url(r'^finance/', views.financeModule, name='financeModule'),
    url(r'^previewing/', views.previewing, name='previewing'),
    url(r'^verifying/', views.verifying, name='verifying'),
    url(r'^previous/', views.previous, name='previous'),
    url(r'^createPayments/', views.createPayments, name='createPayments'),
    url(r'^createReceipts/', views.createReceipts, name='createReceipts'),
    url(r'^previousPayments/', views.previousPayments, name='previousPayements'),
    url(r'^previousReceipts/', views.previousReceipts, name='previousReceipts'),
    url(r'^createBank/', views.createBank, name='createBank'),
    url(r'^createCompany/', views.createCompany, name='createCompany'),
    # url(r'^alterBank/', views.alterBank, name='alterBank'),
    # url(r'^alterCompany/', views.alterCompany, name='alterCompany'),
    url(r'^printSalary', views.printSalary, name='Salary'),

]
