# from django.urls import path
# from django.conf.urls import url
# from django.urls import path
# from rest_framework.urlpatterns import format_suffix_patterns
# from . import views

# app_name = 'inventory'

# urlpatterns = [
#     path('items/', views.ItemListView.as_view(), name='item-list'),
#     path('item/', views.ItemDetailView.as_view(), name='item-detail'),
#     path('item/create/', views.ItemCreateView.as_view(), name='item-create'),
#     path('item/update/', views.ItemUpdateView.as_view(), name='item-update'),
#     path('item/delete/', views.ItemDeleteView.as_view(), name='item-delete'),

#     # Department Info URLs
#     path('departments/', views.DepartmentInfoListView.as_view(), name='department-list'),
#     # path('department/<int:pk>/', views.DepartmentInfoDetailView.as_view(), name='department-detail'),

#     # Relationship URLs
#     # path('relationship/create/', views.RelationshipCreateView.as_view(), name='relationship-create'),

#     # Event URLs
#     # path('events/', views.EventListView.as_view(), name='event-list'),
#     # path('event/create/', views.EventCreateView.as_view(), name='event-create'),
# ]

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from . import views

# app_name = 'inventory'

# # Create a router and register viewsets
# router = DefaultRouter()
# router.register(r'items', views.ItemViewSet, basename='item')
# router.register(r'departments', views.DepartmentInfoViewSet, basename='department')
# router.register(r'sections', views.SectionInfoViewSet, basename='section')

# urlpatterns = [
#     path('api/', include(router.urls)),  # Include all the routes for the viewsets
# ]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import views

router = DefaultRouter()
router.register(r'items', views.ItemViewSet)
router.register(r'departments', views.DepartmentInfoViewSet)
router.register(r'sections', views.SectionInfoViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

