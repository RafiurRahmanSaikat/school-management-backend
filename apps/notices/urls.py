from rest_framework.routers import DefaultRouter

from .views import NoticeViewSet, PublicNoticeListAPIView
from django.urls import path

router = DefaultRouter(trailing_slash=False)
router.register("notices", NoticeViewSet, basename="notice")

urlpatterns = router.urls + [
    path("public/notices/", PublicNoticeListAPIView.as_view(), name="public-notices"),
]
