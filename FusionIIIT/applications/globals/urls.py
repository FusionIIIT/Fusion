from django.conf.urls import url, include

app_name = 'globals'

# globals' own pages were replaced by the React app; only its API is served.
urlpatterns = [
    url(r'^api/', include('applications.globals.api.urls')),
]
