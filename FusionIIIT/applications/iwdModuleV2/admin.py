from django.contrib import admin

from .models import Projects,PageOneDetails,AESDetails,PageTwoDetails,CorrigendumTable,Addendum,PreBidDetails,TechnicalBidDetails,TechnicalBidContractorDetails,FinancialBidDetails,FinancialContractorDetails,LetterOfIntentDetails,WorkOrderForm,Agreement,Milestones,PageThreeDetails,ExtensionOfTimeDetails,NoOfTechnicalBidTimes

# Register your models here.
admin.site.register(Projects)
admin.site.register(PageOneDetails)
admin.site.register(AESDetails)
admin.site.register(PageTwoDetails)
admin.site.register(CorrigendumTable)
admin.site.register(Addendum)
admin.site.register(PreBidDetails)
admin.site.register(TechnicalBidDetails)
admin.site.register(TechnicalBidContractorDetails)
admin.site.register(FinancialBidDetails)
admin.site.register(FinancialContractorDetails)
admin.site.register(LetterOfIntentDetails)
admin.site.register(WorkOrderForm)
admin.site.register(Agreement)
admin.site.register(Milestones)
admin.site.register(PageThreeDetails)
admin.site.register(ExtensionOfTimeDetails)
admin.site.register(NoOfTechnicalBidTimes)
