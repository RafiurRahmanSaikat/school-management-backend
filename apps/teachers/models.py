from django.db import models

from apps.core.models import SocialLinksMixin, TimeStampedModel


class Designation(models.TextChoices):
    HEADTEACHER = "HEADTEACHER", "Headteacher"
    ASSISTANT_HEADTEACHER = "ASSISTANT_HEADTEACHER", "Assistant Headteacher"
    SENIOR_TEACHER = "SENIOR_TEACHER", "Senior Teacher"
    ASSISTANT_TEACHER = "ASSISTANT_TEACHER", "Assistant Teacher"
    STAFF = "STAFF", "Non-teaching Staff"


class Teacher(TimeStampedModel, SocialLinksMixin):
    """
    Everything that is TEACHER-SPECIFIC. Name / email / phone / address /
    gender / profile picture all live on the linked User (apps.accounts) —
    they are NOT repeated here. This model only adds what a teacher record
    needs on top of a normal account: designation, subjects, assigned
    classes, qualifications, employment info.
    """

    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="teacher_profile"
    )
    employee_id = models.CharField(max_length=20, unique=True)
    designation = models.CharField(max_length=30, choices=Designation.choices)
    subjects = models.ManyToManyField(
        "academics.Subject", related_name="teachers", blank=True,
        help_text="Subject(s) this teacher is qualified/assigned to teach.",
    )
    assigned_sections = models.ManyToManyField(
        "academics.Section", related_name="subject_teachers", blank=True,
        help_text="Class-sections this teacher currently takes classes in.",
    )
    education_qualification = models.CharField(
        max_length=255, blank=True, help_text="e.g. M.Sc in Physics, B.Ed"
    )
    joining_date = models.DateField(null=True, blank=True)
    is_active_employee = models.BooleanField(default=True)

    class Meta:
        ordering = ["employee_id"]

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    @property
    def is_class_teacher(self) -> bool:
        return self.class_teacher_of_sections.exists()

    def is_class_teacher_of(self, section_id) -> bool:
        return self.class_teacher_of_sections.filter(pk=section_id).exists()
