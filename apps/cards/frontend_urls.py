from django.urls import path

from .frontend_views import (
    CardGeneratorView,
    GeneratedDocumentDetailView,
    GeneratedDocumentListView,
)

app_name = "cards-frontend"

urlpatterns = [
    path("generate", CardGeneratorView.as_view(), name="generate"),
    path("history", GeneratedDocumentListView.as_view(), name="history"),
    path("history/<int:pk>", GeneratedDocumentDetailView.as_view(), name="document-detail"),
]
