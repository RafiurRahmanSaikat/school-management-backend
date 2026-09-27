"""
Root URL config.

Each app owns its own urls.py (a DRF router + any extra paths); this file
only *includes* them under /api/. Adding a brand-new app therefore never
requires editing an existing app's urls.py — just one new include() line
here.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.notices.views import HomePageView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    # JWT auth
    path("api/auth/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    # Each app's API routes
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.academics.urls")),
    path("api/", include("apps.teachers.urls")),
    path("api/", include("apps.students.urls")),
    path("api/", include("apps.exams.urls")),
    path("api/", include("apps.billing.urls")),
    path("api/", include("apps.notices.urls")),
    path("api/", include("apps.comments.urls")),
    path("api/", include("apps.cards.urls")),
    path("dashboard/cards/", include("apps.cards.frontend_urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
