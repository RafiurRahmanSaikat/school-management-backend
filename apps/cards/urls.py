from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GeneratedDocumentViewSet,
    StudentAdmitCardView,
    StudentIDCardView,
    StudentRegistrationCardView,
    StudentTestimonialView,
)

router = DefaultRouter(trailing_slash=False)
router.register("cards/generated", GeneratedDocumentViewSet, basename="generated-document")

urlpatterns = [
    # Single Student Routes
    path("cards/id/<int:student_id>", StudentIDCardView.as_view(), name="card-id"),
    path(
        "cards/registration/<int:student_id>",
        StudentRegistrationCardView.as_view(),
        name="card-registration",
    ),
    path(
        "cards/admit/<int:student_id>/<int:exam_id>",
        StudentAdmitCardView.as_view(),
        name="card-admit",
    ),
    path(
        "cards/testimonial/<int:student_id>",
        StudentTestimonialView.as_view(),
        name="card-testimonial",
    ),
    # Bulk Generation Routes — filter via ?class_id=&section_id=&group_id=&roll_start=&roll_end=&reg_start=&reg_end=
    path("cards/id/bulk", StudentIDCardView.as_view(), name="card-id-bulk"),
    path(
        "cards/registration/bulk",
        StudentRegistrationCardView.as_view(),
        name="card-registration-bulk",
    ),
    path("cards/admit/bulk", StudentAdmitCardView.as_view(), name="card-admit-bulk"),
    path(
        "cards/testimonial/bulk",
        StudentTestimonialView.as_view(),
        name="card-testimonial-bulk",
    ),
    # Generated-document history (read-only)
    path("", include(router.urls)),
]
