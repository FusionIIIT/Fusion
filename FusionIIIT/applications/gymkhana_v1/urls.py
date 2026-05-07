from django.urls import include, path


app_name = "gymkhana_v1"

urlpatterns = [
    path("api/", include("applications.gymkhana_v1.api.urls")),
]
