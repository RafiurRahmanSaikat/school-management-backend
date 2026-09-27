from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class DocumentType(models.TextChoices):
    ID_CARD = "ID_CARD", "Student ID Card"
    REGISTRATION_CARD = "REGISTRATION_CARD", "Registration Card"
    ADMIT_CARD = "ADMIT_CARD", "Admit Card"
    TESTIMONIAL = "TESTIMONIAL", "Testimonial"


class DocumentLanguage(models.TextChoices):
    EN = "EN", "English"
    BN = "BN", "Bangla"


class GeneratedDocument(TimeStampedModel):
    """
    A record of one generated PDF batch (single student or bulk). The actual
    PDF bytes are saved to MEDIA_ROOT via `file`; this row is what lets the
    Django frontend show "documents generated so far" with a download link,
    instead of every generated PDF only ever existing as a one-off HTTP
    response that's gone once downloaded.
    """

    doc_type = models.CharField(max_length=30, choices=DocumentType.choices)
    language = models.CharField(
        max_length=2, choices=DocumentLanguage.choices, default=DocumentLanguage.EN,
        help_text="Only meaningful for TESTIMONIAL; EN/BN otherwise ignored.",
    )
    file = models.FileField(upload_to="generated_documents/%Y/%m/%d/")
    student_count = models.PositiveIntegerField(default=0)
    filter_summary = models.CharField(
        max_length=255, blank=True,
        help_text="Human-readable description of the filters used, e.g. 'Class 10 - Section A - Science'.",
    )
    exam = models.ForeignKey(
        "exams.Exam", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="generated_admit_cards",
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="generated_documents",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_doc_type_display()} x{self.student_count} ({self.created_at:%Y-%m-%d %H:%M})"
