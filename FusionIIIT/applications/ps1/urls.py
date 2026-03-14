from django.conf.urls import url,include

from . import views

app_name = 'ps1'

urlpatterns = [

    url(r'^$', views.ps1, name='ps1'),
    url(r'^create_proposal/$', views.create_proposal, name='create_proposal'),
    # url(r'^compose_indent/$', views.compose_indent, name='compose_indent'),
    url(r'^composed_indents/$', views.composed_indents, name='composed_indents'),

    # here id is the Holdsdesignation id.
    url(r'^indentview/(?P<id>\d+)/$', views.indentview, name='indentview'),
    url(r'^archieveview/(?P<id>\d+)/$', views.archieveview, name='archieveview'),

    url(r'^drafts/$', views.drafts, name='drafts'),
    url(r'^draftview/(?P<id>\d+)/$', views.draftview, name='draftview'),
    url(r'^inwardIndent/$', views.inward, name='inward'),

    # indentview2 is to get all the indentFiles inwarded towards the request.user.

    url(r'^indentview2/(?P<id>\d+)/$', views.indentview2, name='indentview2'),
    url(r'^confirmdelete/(?P<id>\d+)/$', views.confirmdelete, name='confirm_delete'),
    url(r'^delete/(?P<id>\d+)/$',views.delete, name='delete'),
    # forward Indent is to see a specific forwarded indent to ourselves 
    url(r'^forwardindent/(?P<id>\d+)/$', views.forwardindent, name='forwardindent'),
    url(r'^createdindent/(?P<id>\d+)/$', views.createdindent, name='createdindent'),
    url(r'^forwardedIndent/(?P<id>\d+)/$', views.forwardedIndent, name='forwardedIndent'),
    
    url(r'^entry/$', views.entry, name='entry'),
    url(r'^StockEntry/$', views.Stock_Entry, name='Stock_Entry'),

    # stock_view is now stock_entry_view which will tell us about the new stock that is entered in any department via a new StockEntry
    url(r'^stock_entry_view/$', views.stock_entry_view, name='stock_view'),

    # current_stock_view will tell us about the current situation of stocks present in any department (both transferred to the department and new stocks added in the department)
    url(r'^current_stock_view/$', views.current_stock_view, name='current_stock_view'),

    # to display individual items belonging to a certain stock entry record.
    url(r'^stock_entry_item_view/$', views.stock_entry_item_view, name='stock_entry_item_view'),

    # to display stock items which are having similar item_type ,grade and department.(used in current_stock_view)
    url(r'^stock_item_view/$', views.stock_item_view, name='stock_item_view'),

    url(r'^archieved_indents/$', views.archieved_files, name='archieved_indents_view'),




    url(r'^stock_delete/$', views.stock_delete, name='stock_delete'),
    url(r'^stock_edit/$', views.stock_edit, name='stock_edit'),
    url(r'^stock_update/$', views.stock_update, name='stock_update'),
    url(r'^stock_login/$', views.dealing_assistant, name='dealing_assistant'),


    url(r'^generate_report/$', views.generate_report, name='generate_report'),
    url(r'^report/$', views.report, name='report'), # !not clear 
    url(r'view-bill/<int:stock_entry_id>/$', views.view_bill, name='view_bill'),
    

    url(r'^perform_transfer/$', views.perform_transfer, name='perform_transfer'),
    url(r'^stock_transfer/$', views.stock_transfer, name='stock_transfer'),
    url(r'^view_transfer/$', views.view_transfer, name='view_transfer'),

    url(r'^outboxview2/(?P<id>\d+)/$', views.outboxview2, name='outboxview2'),
    url(r'^outboxview/$', views.outboxview, name='outboxview'),


    url(r'^update_stock_item_inUse/$', views.updateStockItemInUse, name='stockItemInUse'),
    url(r'^item_detail/(?P<id>\d+)/$', views.item_detail, name='item_detail'),

    # BASE API 
    url(r'^api/',include('applications.ps1.api.urls')),

]
