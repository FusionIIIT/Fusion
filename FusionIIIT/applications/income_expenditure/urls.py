from django.conf.urls import url

from . import views
appname = 'income_expenditure'
urlpatterns = [
    url(r'^main/', views.main_page, name='main-page'),
    url(r'^addIncome/', views.add_income, name='add-income'),
    url(r'^addIncomeSource/', views.add_income_source, name='add-income-source'),
    url(r'^addExpenditure/', views.add_expenditure, name='add-expenditure'),
    url(r'^addExpenditureType/', views.add_expenditure_type, name='add-expenditure-type'),
    url(r'^deleteExpenditureHistory/',views.del_expenditure,name='del-expenditure'),
    url(r'^deleteIncomeHistory/',views.del_income,name='del-income'),
    url(r'^balanceSheet_pdf/',views.balanceSheet,name='balance-sheet'),
    url(r'^updateFixedValues/',views.updateFixedValues,name='fixed-values'),
    url(r'^viewIncomeStats/',views.view_income_stats,name='view-income-stats'),
    url(r'^viewExpenditureStats/',views.view_expenditure_stats,name='view-expenditure-stats'),
]
