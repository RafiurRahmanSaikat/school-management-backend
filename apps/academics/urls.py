from rest_framework.routers import DefaultRouter

from .views import (
    AcademicYearViewSet,
    GroupViewSet,
    SchoolClassViewSet,
    SectionViewSet,
    SubjectViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register("academic-years", AcademicYearViewSet, basename="academicyear")
router.register("classes", SchoolClassViewSet, basename="schoolclass")
router.register("groups", GroupViewSet, basename="group")
router.register("sections", SectionViewSet, basename="section")
router.register("subjects", SubjectViewSet, basename="subject")

urlpatterns = router.urls
