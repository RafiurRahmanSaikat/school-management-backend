from rest_framework.routers import DefaultRouter

from .views import TeacherViewSet

router = DefaultRouter(trailing_slash=False)
router.register("teachers", TeacherViewSet, basename="teacher")

urlpatterns = router.urls
