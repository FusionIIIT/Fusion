from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import views
from .api.views import ItemCountView

router = DefaultRouter()
router.register(r'items', views.ItemViewSet)
router.register(r'departments', views.DepartmentInfoViewSet)
router.register(r'sections', views.SectionInfoViewSet)
router.register(r'requests', views.InventoryRequestViewSet, basename='inventoryrequest')

urlpatterns = [
    path('api/', include(router.urls)),
    path("api/item-count/", ItemCountView.as_view(), name="item-count"),
]
