from django.conf.urls import url

from . import views

app_name = 'ps1'

urlpatterns = [

    url(r'^$', views.ps1, name='ps1'),
    # url(r'^compose_indent/$', views.compose_indent, name='compose_indent'),
    url(r'^composed_indents/$', views.composed_indents, name='composed_indents'),
    url(r'^indentview/(?P<id>\d+)$', views.indentview, name='indentview'),
    url(r'^drafts/$', views.drafts, name='drafts'),
    url(r'^draftview/(?P<id>\d+)$', views.draftview, name='draftview'),
    url(r'^inwardIndent/$', views.inward, name='inward'),
    url(r'^indentview2/(?P<id>\d+)$', views.indentview2, name='indentview2'),
    url(r'^confirmdelete/(?P<id>\d+)$', views.confirmdelete, name='confirm_delete'),
    url(r'^delete/(?P<id>\d+)$',views.delete, name='delete'),
    url(r'^forwardindent/(?P<id>\d+)/$', views.forwardindent, name='forwardindent'),
    url(r'^createdindent/(?P<id>\d+)/$', views.createdindent, name='createdindent'),
    url(r'^StockEntry/$', views.Stock_Entry, name='Stock_Entry'),
    url(r'^stock_view/$', views.stock_view, name='stock_view'),
    url(r'^stock_delete/$', views.stock_delete, name='stock_delete'),
    url(r'^stock_edit/$', views.stock_edit, name='stock_edit'),
    url(r'^stock_update/$', views.stock_update, name='stock_update'),
    url(r'^entry/$', views.entry, name='entry'),
    url(r'^stock_login/$', views.dealing_assistant, name='dealing_assistant')
]
