from django.conf.urls import url

from . import views

urlpatterns = [
    # to create a new indent file
    url(r'^create_proposal/', views.createProposal, name='create-proposal'),

    # PENDING : TO CREATE A INDENT FILE DRAFT

    # GET DESIGNATIONS USING USER TOKEN 
    url(r'^getDesignations/', views.getDesignations, name='get-designations'),

    # to get the indent files created by the user
    url(r'^indentview/(?P<id>\d+)$', views.indentView, name='indent-view'),

    # to get the indent Files drafts by a user
    url(r'^draftview/(?P<id>\d+)$', views.draftView, name='draft-view'),
    
    # to get all the indent files inwarded to the user  'id' is holdsDesignation id.
    url(r'^inwardIndents/(?P<id>\d+)$', views.inwardIndents, name='inward-indents'),

    # to see the details of a specifc indent file
    url(r'^indentFile/(?P<id>\d+)$', views.indentFile, name='indent-file'),

    # to forward a indent File
    url(r'^indentFile/forward/(?P<id>\d+)$', views.ForwardIndentFile, name='forward-indent-file'),

    # STOCKS API
    # to return all the indent files (GET) as well as to get the information of any specific indent file (POST) to further add stock to it (just info).
    url(r'^entry/(?P<id>\d+)$', views.entry, name='entry'),

    # To add stock corresponding to a Indent File
    url(r'^stockEntry/(?P<id>\d+)$', views.stockEntry, name='stock-entry'),

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
]
