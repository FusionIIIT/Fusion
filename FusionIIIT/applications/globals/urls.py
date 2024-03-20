from django.conf.urls import url, include

from . import views

app_name = 'globals'

urlpatterns = [

    url(r'^$', views.index, name='index'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^about/', views.about, name='about'),
    # generic profile endpoint, displays or redirects appropriately
    url(r'^profile/(?P<username>.+)/$', views.profile, name='profile'),
    # profile of currently logged user
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^search/$', views.search, name='search'),
    # Feedback and issues url
    url(r'^feedback/$', views.feedback, name="feedback"),
    url(r'^issue/$', views.issue, name="issue"),
    url(r'^view_issue/(?P<id>\d+)/$', views.view_issue, name="view_issue"),
    url(r'^support_issue/(?P<id>\d+)/$', views.support_issue, name="support_issue"),
    url(r'^logout/$', views.logout_view, name="logout_view"),
    # Endpoint to reset all passwords in DEV environment
    url(r'^resetallpass/$', views.reset_all_pass, name='resetallpass'),
    # API urls
    url(r'^api/', include('applications.globals.api.urls')),
    url(r'^update_global_variable/$', views.update_global_variable, name='update_global_var'),
]
