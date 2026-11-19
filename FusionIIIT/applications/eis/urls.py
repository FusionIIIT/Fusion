from django.conf.urls import include, url

app_name = 'eis'
urlpatterns = [
    url(r'^api/', include('applications.eis.api.urls')),
]
