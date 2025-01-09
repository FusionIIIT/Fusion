from django.conf.urls import url
from django.urls import path
from . import views

urlpatterns = [
    # to create a new indent file
    url(r'^create_proposal/', views.createProposal, name='create-proposal'),
    url(r'^create_draft/', views.createDraft, name='create-draft'),
    url(r'^delete_indent/', views.delete_indent, name='delete-indents'),
    url(r'^view_indent/', views.getOneFiledIndent, name='view-indent'),
    # path('create_indent/<int:id>/', views.createIndent, name='create-indent'),
    path('forward_indent/<int:id>/', views.forwardIndent, name='create-indent'),
    # PENDING : TO CREATE A INDENT FILE DRAFT
    path('user-suggestions', views.user_suggestions, name='user-suggestions'),
    # GET DESIGNATIONS USING USER TOKEN 
    url(r'^getDesignations/', views.getDesignations, name='get-designations'),

    # to get the indent files created by the user
    path('indentview/<str:username>/', views.indentView, name='indent-view'),
    path('indentview2/<str:username>/', views.indentView2, name='indent-view2'),
    # url(r'^indentview2/(?P<id>\d+)$', views.indentView2, name='indent-view2'),

    # to get the indent Files drafts by a user
    path('draftview/<str:username>/', views.draftView, name='draft-view'),
    
    # to get all the indent files inwarded to the user  'id' is holdsDesignation id.
    url(r'^inwardIndents/(?P<id>\d+)$', views.inwardIndents, name='inward-indents'),


    # url(r'^outboxview2/(?P<id>\d+)/$', views.outboxview2, name='outboxview2'),


    # to see the details of a specifc indent file
    url(r'^indentFile/(?P<id>\d+)$', views.indentFile, name='indent-file'),

    # to forward a indent File
    url(r'^indentFile/forward/(?P<id>\d+)$', views.ForwardIndentFile, name='forward-indent-file'),

    # STOCKS API
    # to return all the indent files (GET) as well as to get the information of any specific indent file (POST) to further add stock to it (just info).
    url(r'^entry/(?P<id>\d+)$', views.entry, name='entry'),

    # To add stock corresponding to a Indent File
    # url(r'^stockEntry/(?P<id>\d+)$', views.stockEntry, name='stock-entry'),

    # To view all the stock entry details
    url(r'^stock_entry_view/(?P<id>\d+)$', views.stockEntryView, name='stock-entry-view'),


    # To view the current_stock_view based on filters
    url(r'^current_stock_view/(?P<id>\d+)$', views.currentStockView, name='current-stock-view'),

    # to view all the items present in any stock entry
    url(r'^stock_entry_item_view/(?P<id>\d+)$', views.stock_entry_item_view, name='stock-entry-item-view'),

    # to delete any stock entry
    url(r'^stock_item_delete/(?P<id>\d+)$', views.stockDelete, name='stock-delete'),

    url(r'^stock_transfer/(?P<id>\d+)$', views.stockTransfer, name='stock-transfer'),

    
    url(r'^perform_transfer/(?P<id>\d+)$', views.performTransfer, name='perform-transfer'),
    # url(r'^archieveview/(?P<id>\d+)$', views.archieveview, name='archievedview'),

    url(r'^archieve_indent/(?P<id>\d+)/$', views.archieve_file, name='archieve-file'),

    path('archieveview/<str:username>/', views.archieveview, name='archievedview'),
    path('outboxview2/<str:username>/', views.outboxview2, name='outboxview2'),
    path('stockEntry/<str:username>/', views.stockEntry, name='stock-entry'),
]