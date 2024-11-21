from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import TransferProductView

router = DefaultRouter()
router.register(r'items', views.ItemViewSet)
router.register(r'departments', views.DepartmentInfoViewSet)
router.register(r'sections', views.SectionInfoViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/transfer_product/', TransferProductView.as_view(), name='transfer_product'),
]
