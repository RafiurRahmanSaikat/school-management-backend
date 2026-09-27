from rest_framework.routers import DefaultRouter

from .views import TeacherCommentViewSet

router = DefaultRouter(trailing_slash=False)
router.register("comments", TeacherCommentViewSet, basename="teachercomment")

urlpatterns = router.urls
