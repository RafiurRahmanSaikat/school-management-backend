from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrReadOnly

from .models import Notice
from .serializers import NoticeSerializer


class NoticeViewSet(viewsets.ModelViewSet):
    """Anyone logged in can read; only admin/headteacher can publish/edit."""

    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ["category", "is_published", "pin_to_top"]

    def perform_create(self, serializer):
        serializer.save(published_by=self.request.user)


class PublicNoticeListAPIView(APIView):
    """Unauthenticated JSON feed of published notices — for the public homepage."""

    permission_classes = [AllowAny]

    def get(self, request):
        notices = Notice.objects.filter(
            is_published=True, published_at__lte=timezone.now()
        )
        return Response(NoticeSerializer(notices, many=True).data)


class HomePageView(TemplateView):
    """
    Public school homepage — renders published notices in proper Bangla
    typography (Noto Sans Bengali, loaded from Google Fonts). This is plain
    server-rendered HTML (no login needed), separate from the JSON API above
    which a future React/mobile frontend would use instead.
    """

    template_name = "notices/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notices"] = Notice.objects.filter(
            is_published=True, published_at__lte=timezone.now()
        )
        return context
