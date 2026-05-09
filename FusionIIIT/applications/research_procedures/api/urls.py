from rest_framework.routers import DefaultRouter
from .views import PatentViewSet

router = DefaultRouter()
router.register(r'patent', PatentViewSet)

urlpatterns = router.urls
print("URL patterns",urlpatterns)