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
    url(r'^stock_login/$', views.dealing_assistant, name='dealing_assistant'),
    url(r'^create_indent_multiple/$',views.create_indent_multiple, name='create_indent_multiple'),
    url(r'^drafts1/$', views.drafts_for_multiple_item, name='drafts_for_multiple_item'),
    url(r'^draftview1/(?P<id>\d+)$', views.draftview_multiple_items_indent, name='draftview_multiple_items_indent'),
    url(r'^drafted_indent/(?P<id>\d+)/$', views.drafted_indent, name='drafted_indent'),
    url(r'^composed_indents_multiple/$', views.composed_indents_multiple, name='composed_indents_multiple'),
    url(r'^filled_indent_list/(?P<id>\d+)$', views.filled_indent_list, name='filled_indent_list'),
    url(r'^view_my_indent/(?P<id>\d+)/$', views.view_my_indent, name='view_my_indent'),
    url(r'^confirmdeletemultiple/(?P<id>\d+)$', views.confirmdeletemultiple, name='confirmdeletemultiple'),
    url(r'^delete_multiple/(?P<id>\d+)$',views.delete_multiple, name='delete_multiple'),
    url(r'^inwardIndentMultiple/$', views.inward_multiple, name='inward_multiple'),
    url(r'^inbox_indent_list/(?P<id>\d+)$', views.inboxlist, name='inbox_indent_list'),
    url(r'^inward_indent_details/(?P<id>\d+)/$', views.inward_indent_details, name='inward_indent_details'),
    url(r'^reject_indent/(?P<id>\d+)/$', views.reject_indent, name='reject_indent'),
    url(r'^item_purchase/(?P<id>\d+)/$', views.item_purchase, name='item_purchase'),
    url(r'^get_designations/$', views.get_designations,name='get_designations')

]
