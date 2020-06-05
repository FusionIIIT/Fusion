from django.conf.urls import url

from . import views

app_name = 'finance'

urlpatterns = [

    url(r'^finance/', views.financeModule, name='financeModule'),
    url(r'^previewing/', views.previewing, name='previewing'),
    url(r'^verifying/', views.verifying, name='verifying'),
    url(r'^previous/', views.previous, name='previous'),

]
