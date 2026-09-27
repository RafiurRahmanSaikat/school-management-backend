from rest_framework.routers import DefaultRouter

from .views import ExamResultViewSet, ExamViewSet, MarkEntryViewSet

router = DefaultRouter(trailing_slash=False)
router.register("exams", ExamViewSet, basename="exam")
router.register("mark-entries", MarkEntryViewSet, basename="markentry")
router.register("exam-results", ExamResultViewSet, basename="examresult")

urlpatterns = router.urls
