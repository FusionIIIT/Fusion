from django.urls import include, path

from applications.visitor_hostel.api.views import VisitorHostelApiHealthView


app_name = "visitorhostel"

urlpatterns = [
    path("", VisitorHostelApiHealthView.as_view(), name="visitorhostel"),
    path("api/", include("applications.visitor_hostel.api.urls")),
]
