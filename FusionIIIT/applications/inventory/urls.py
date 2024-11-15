from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.ItemListView.as_view(), name='item-list'),
    path('item/', views.ItemDetailView.as_view(), name='item-detail'),
    path('item/create/', views.ItemCreateView.as_view(), name='item-create'),
    path('item/update/', views.ItemUpdateView.as_view(), name='item-update'),
    path('item/delete/', views.ItemDeleteView.as_view(), name='item-delete'),

    # Department Info URLs
    path('departments/', views.DepartmentInfoListView.as_view(), name='department-list'),
    # path('department/<int:pk>/', views.DepartmentInfoDetailView.as_view(), name='department-detail'),

    # Relationship URLs
    path('relationship/create/', views.RelationshipCreateView.as_view(), name='relationship-create'),

    # Event URLs
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('event/create/', views.EventCreateView.as_view(), name='event-create'),
]
