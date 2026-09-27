"""
The Student record.

Design notes (read this before adding fields elsewhere):
- Class + Section + Group are NOT duplicated here — a student just points at
  one `academics.Section`, and that Section already carries the SchoolClass
  and Group. Want "all Class 9 Science students"? Filter
  Student.objects.filter(section__school_class__level=9, section__group__code="SCI").
- Marks / GPA live in apps.exams (MarkEntry, ExamResult) and are looked up via
  `student.mark_entries` / `student.results` (reverse FK) — not stored here,
  so a student can have many exams over many years without this table growing
  columns.
- Bills / payments live in apps.billing (Bill, Payment) via `student.bills`.
- Teacher comments live in apps.comments (TeacherComment) via `student.comments`.
This keeps Student itself lean while still letting admin/headteacher/class
teacher pull "everything about this student" together in one serializer
(see serializers.StudentDetailSerializer) without the table itself becoming
an ever-growing grab-bag.
"""
from django.db import models

from apps.core.models import BloodGroup, PersonMixin, TimeStampedModel, UUIDModel


class Religion(models.TextChoices):
    ISLAM = "ISLAM", "Islam"
    HINDU = "HINDU", "Hindu"
    BUDDHIST = "BUDDHIST", "Buddhist"
    CHRISTIAN = "CHRISTIAN", "Christian"
    OTHER = "OTHER", "Other"


class StudentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    TRANSFERRED = "TRANSFERRED", "Transferred out"
    GRADUATED = "GRADUATED", "Graduated"
    SUSPENDED = "SUSPENDED", "Suspended"
    DROPPED = "DROPPED", "Dropped out"


class GuardianRelation(models.TextChoices):
    FATHER = "FATHER", "Father"
    MOTHER = "MOTHER", "Mother"
    UNCLE = "UNCLE", "Uncle"
    AUNT = "AUNT", "Aunt"
    GRANDFATHER = "GRANDFATHER", "Grandfather"
    GRANDMOTHER = "GRANDMOTHER", "Grandmother"
    OTHER = "OTHER", "Other"


class Student(TimeStampedModel, UUIDModel, PersonMixin):
    # --- identity ---
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    religion = models.CharField(max_length=20, choices=Religion.choices, default=Religion.ISLAM)
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices, blank=True)

    # --- academic placement ---
    section = models.ForeignKey(
        "academics.Section", on_delete=models.PROTECT, related_name="students"
    )
    roll_no = models.PositiveIntegerField(help_text="Roll number within the section for the year.")
    registration_no = models.CharField(
        max_length=30, unique=True, help_text="Permanent board/school registration number."
    )
    optional_fourth_subject = models.ForeignKey(
        "academics.Subject", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="students_taking_as_fourth",
        help_text="The student's chosen 4th/optional subject (bonus GPA point).",
    )

    # --- admission / history ---
    admission_date = models.DateField(null=True, blank=True)
    previous_school = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=StudentStatus.choices, default=StudentStatus.ACTIVE)

    # --- guardians ---
    father_name = models.CharField(max_length=150, blank=True)
    father_phone = models.CharField(max_length=20, blank=True)
    father_occupation = models.CharField(max_length=150, blank=True)
    mother_name = models.CharField(max_length=150, blank=True)
    mother_phone = models.CharField(max_length=20, blank=True)
    mother_occupation = models.CharField(max_length=150, blank=True)
    guardian_relation = models.CharField(
        max_length=20, choices=GuardianRelation.choices, default=GuardianRelation.FATHER,
        help_text="Who the primary contact guardian is, if not living with parents.",
    )
    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["section", "roll_no"]
        unique_together = [("section", "roll_no")]
        indexes = [
            models.Index(fields=["section", "roll_no"]),
            models.Index(fields=["registration_no"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.registration_no})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def school_class(self):
        return self.section.school_class

    @property
    def group(self):
        return self.section.group

    # --- convenience aggregates pulling from other apps' reverse relations ---
    @property
    def total_due(self):
        from django.db.models import Sum

        agg = self.bills.aggregate(total=Sum("amount_due"), paid=Sum("amount_paid"))
        return (agg["total"] or 0) - (agg["paid"] or 0)
