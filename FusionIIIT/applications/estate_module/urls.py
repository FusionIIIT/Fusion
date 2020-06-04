from django.urls import path

from . import views

urlpatterns = [
    path('old', views.oldEstate, name="old"),
    path('', views.estate, name="estate"),
    path('new', views.newEstate, name="new_estate"),
    path('edit/<estate_id>', views.editEstate, name="edit_estate"),
    path('delete/<estate_id>', views.deleteEstate, name="delete_estate"),
]
