from django.conf.urls import url

from . import views

app_name = 'iwdModuleV2'

urlpatterns = [


    url(r'^$', views.dashboard, name='IWD Dashboard'),
    url(r'^page1_1/$', views.page1_1, name='IWD Page1.1'),
    url(r'page2_1/$', views.page2_1, name='IWD Page2.1'),
    url(r'corrigendumInput/$', views.corrigendumInput, name='Corrigendum Input'),
    url(r'addendumInput/$', views.addendumInput, name='Addendum Input'),
    url(r'milestoneForm/$', views.milestonesForm, name='Milestone Form'),
    url(r'technicalBidForm/$', views.TechnicalBidForm, name='Technical Bid Form'),
    url(r'extensionForm/$', views.ExtensionOfTimeForm, name='Extension Form'),
    url(r'letterOfIntent/$', views.letterOfIntent, name='Letter Of Intent Input'),
    url(r'workOrderForm/$', views.workOrderForm, name='Work Order Form'),
    url(r'agreement/$', views.AgreementInput, name='Agreement Input'),
    url(r'page3_1/$', views.page3_1, name='IWD Page 3.1'),
    url(r'noOfEntriesTechnicalBid/$', views.noOfEntriesTechnicalBid, name='IWD Technical Bid'),
    url(r'noOfEntriesFinancialBid/$', views.noOfEntriesFinancialBid, name='IWD Financial Bid'),
    url(r'page1View/$', views.page1View, name='Page 1 Views'),
    url(r'page2View/$', views.page2View, name='Page 2 View'),
    url(r'page3View/$', views.page3View, name='Page 3 View'),
    url(r'extensionFormView/$', views.extensionFormView, name='Extension Form'),
    url(r'AESView/$', views.AESView, name='AES View'),
    url(r'financialBidView/$', views.financialBidView, name='Financial Bid View'),
    url(r'preBidForm/$', views.PreBidForm, name='Pre Bid Form'),
    url(r'AESForm/$', views.AESForm, name='AESForm'),
    url('workOrderFormView/$', views.workOrderFormView, name='Work Order Form View'),
    url(r'letterOfIntentView', views.letterOfIntentView, name='Letter Of Intent View'),
    url(r'preBidDetailsView/$', views.preBidDetailsView, name='Pre Bid Details View'),
    url(r'technicalBidView/$', views.technicalBidView, name='Technical Bid View'),
    url(r'milestoneView/$', views.milestoneView, name='Milestones'),
    url(r'addendumView/$', views.addendumView, name='Addendum View'),
    url('agreementView/$', views.agreementView, name='Agreement VIew'),
    url(r'corrigendumView/$', views.corrigendumView, name='Corrigendum View')
]
