from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class NoticeCategory(models.TextChoices):
    GENERAL = "GENERAL", "General"
    EXAM = "EXAM", "Exam"
    ADMISSION = "ADMISSION", "Admission"
    HOLIDAY = "HOLIDAY", "Holiday"
    RESULT = "RESULT", "Result"
    URGENT = "URGENT", "Urgent"


class Notice(TimeStampedModel):
    """
    Homepage notice board entry. `title` / `body` are plain CharField/TextField
    — Django's TextField is UTF-8 by default so Bangla (or any unicode) text
    is stored and returned exactly as typed; the *rendering* in proper Bangla
    typography (Noto Sans Bengali) happens in the homepage template
    (templates/notices/home.html), not in the model.
    """

    title = models.CharField(max_length=255, help_text="Bangla or English, e.g. 'বার্ষিক পরীক্ষার সময়সূচি'")
    body = models.TextField(help_text="Full notice text — Bangla unicode supported natively.")
    category = models.CharField(max_length=20, choices=NoticeCategory.choices, default=NoticeCategory.GENERAL)
    attachment = models.FileField(upload_to="notices/", null=True, blank=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    published_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="notices_published"
    )
    pin_to_top = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pin_to_top", "-published_at"]

    def __str__(self):
        return self.title
