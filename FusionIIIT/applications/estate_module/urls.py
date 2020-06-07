from django.urls import path

from . import views

urlpatterns = [
    path('', views.estate, name="estate_module_home"),
    path('new/estate', views.newEstate, name="new_estate"),
    path('edit/estate/<estate_id>', views.editEstate, name="edit_estate"),
    path('delete/<estate_id>', views.deleteEstate, name="delete_estate"),
    path('new/work', views.newWork, name="new_work"),
    path('edit/work/<work_id>', views.editWork, name="edit_work"),
    path('delete/work/<work_id>', views.deleteWork, name="delete_work"),
]
