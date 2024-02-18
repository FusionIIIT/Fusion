from django.conf.urls import url
from . import views
from .views import *

urlpatterns = [
    url("feedbackApi", views.FeedbackApi.as_view(), name="feedbackApi"),
    url("menuChangeRequestApi", views.Menu_change_requestApi.as_view(), name="menuChangeRequestApi"),
    url("messMinutesApi", views.Mess_minutesApi.as_view(), name="messMinutesApi"),
    # url("nonvegDataApi", views.Nonveg_dataApi.as_view(), name="nonvegDataApi"),
    url("specialRequestApi", views.Special_requestApi.as_view(), name="specialRequestApi"),
    url("messMeetingApi", views.Mess_meetingApi.as_view(), name="messMeetingApi"),
    # url("nonvegMenuApi", views.Nonveg_menuApi.as_view(), name="nonvegMenuApi"),
    url("vacationFoodApi", views.Vacation_foodApi.as_view(), name="vacationFoodApi"),
    url("messInfoApi", views.MessinfoApi.as_view(), name="messInfoApi"),
    url("rebateApi", views.RebateApi.as_view(), name="rebateApi"),
    url("menuApi", views.MenuApi.as_view(), name="menuApi"),
    url("paymentsApi", views.PaymentsApi.as_view(), name="paymentsApi"),
    url("monthlyBillApi", views.Monthly_billApi.as_view(), name="monthlyBillApi"),
    url("messBillBaseApi", views.MessBillBaseApi.as_view(), name="messBillBaseApi"),
    url("messRegApi", views.Mess_regApi.as_view(), name="messRegApi"),
]