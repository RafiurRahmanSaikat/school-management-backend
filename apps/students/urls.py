from rest_framework.routers import DefaultRouter

from .views import StudentViewSet

router = DefaultRouter(trailing_slash=False)
router.register("students", StudentViewSet, basename="student")

urlpatterns = router.urls
