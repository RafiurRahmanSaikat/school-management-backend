"""
The "shape" of the school: which classes exist (Form 6-10), which sections
(A/B) each class has per year, which SSC groups exist (Science/Commerce/
Arts), and the NCTB subject + marks-distribution table.

This app has NO idea about students or teachers — it just describes the
academic structure, so students/teachers/exams all depend on it instead of it
depending on them. That keeps the dependency graph one-directional and easy
to reason about when adding features later.
"""

from django.db import models

from apps.core.models import TimeStampedModel


class AcademicYear(TimeStampedModel):
    year = models.PositiveIntegerField(unique=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-year"]

    def __str__(self):
        return str(self.year)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)


class SchoolClass(TimeStampedModel):
    """Form 6, Form 7, ... Form 10 (i.e. Bangladeshi "Class 6" .. "Class 10")."""

    LEVEL_CHOICES = [(n, f"Class {n}") for n in range(6, 11)]

    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, unique=True)
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["level"]

    def __str__(self):
        return self.name or f"Class {self.level}"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"Class {self.level}"
        super().save(*args, **kwargs)


class Group(TimeStampedModel):
    """
    SSC groups: Science / Commerce / Arts (Humanities). Relevant mainly for
    Class 9 & 10. Lower classes use the "General" group (no group split yet).
    Modeled as a table (not hard-coded choices) so admin can rename / add a
    group later (e.g. a vocational track) without a code change.
    """

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Section(TimeStampedModel):
    """A concrete class+section for a given academic year, e.g. 'Class 9 - A - 2026'."""

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name="sections"
    )
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name="sections"
    )
    name = models.CharField(max_length=10, help_text="A, B, C ...")
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Leave blank for classes that aren't grouped yet (typically 6-8).",
    )
    class_teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_teacher_of_sections",
        help_text="The single class teacher responsible for this section.",
    )
    capacity = models.PositiveIntegerField(default=60)

    class Meta:
        ordering = ["academic_year", "school_class__level", "name"]
        unique_together = [("academic_year", "school_class", "name", "group")]

    def __str__(self):
        group_part = f" ({self.group.code})" if self.group_id else ""
        return f"{self.school_class} - {self.name}{group_part} [{self.academic_year}]"


class SubjectCategory(models.TextChoices):
    COMPULSORY = "COMPULSORY", "Compulsory"
    SCIENCE = "SCIENCE", "Science"
    COMMERCE = "COMMERCE", "Commerce"
    ARTS = "ARTS", "Arts/Humanities"
    OPTIONAL_4TH = "OPTIONAL_4TH", "Optional / 4th"
    SPECIAL = "SPECIAL", "Special"


class Subject(TimeStampedModel):
    """
    One row per NCTB SSC subject exactly as per the official marks
    distribution table. `is_fourth_subject_candidate` marks the subjects that
    a student may take as their bonus 4th subject (per their group).
    """

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10, unique=True)
    category = models.CharField(max_length=20, choices=SubjectCategory.choices)
    total_marks = models.PositiveSmallIntegerField()
    cq_marks = models.PositiveSmallIntegerField(
        default=0, help_text="Creative/Written question marks"
    )
    mcq_marks = models.PositiveSmallIntegerField(default=0)
    practical_marks = models.PositiveSmallIntegerField(default=0)
    is_fourth_subject_candidate = models.BooleanField(default=False)
    applicable_classes = models.ManyToManyField(
        SchoolClass,
        related_name="subjects",
        blank=True,
        help_text="Which classes (6-10) this subject is taught in.",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean_total(self) -> int:
        return self.cq_marks + self.mcq_marks + self.practical_marks
