from decimal import Decimal

from django.db import models

from apps.core.models import TimeStampedModel

from .grading import GradeResult, grade_for_marks


class ExamType(models.TextChoices):
    CLASS_TEST = "CLASS_TEST", "Class Test"
    FIRST_TERM = "FIRST_TERM", "First Term / Half Yearly"
    SECOND_TERM = "SECOND_TERM", "Second Term"
    PRE_TEST = "PRE_TEST", "Pre-Test"
    TEST_EXAM = "TEST_EXAM", "Test Exam (Pre-SSC)"
    FINAL = "FINAL", "Final / Annual Exam"
    SSC = "SSC", "SSC Board Exam"


class Exam(TimeStampedModel):
    name = models.CharField(max_length=150)
    exam_type = models.CharField(max_length=20, choices=ExamType.choices)
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.CASCADE, related_name="exams")
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.CASCADE, related_name="exams")
    date = models.DateField()

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.name} - {self.school_class} ({self.academic_year})"


class MarkEntry(TimeStampedModel):
    """One row = one student's marks in one subject for one exam."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="mark_entries")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="mark_entries")
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT, related_name="mark_entries")

    cq_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    mcq_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    practical_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))

    # cached, recomputed on every save() so reports never need to redo the math
    total_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    letter_grade = models.CharField(max_length=2, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))

    entered_by = models.ForeignKey(
        "teachers.Teacher", on_delete=models.SET_NULL, null=True, blank=True, related_name="marks_entered"
    )

    class Meta:
        ordering = ["exam", "student", "subject"]
        unique_together = [("exam", "student", "subject")]

    def __str__(self):
        return f"{self.student} - {self.subject.code} - {self.exam}"

    @property
    def is_fourth_subject(self) -> bool:
        return self.student.optional_fourth_subject_id == self.subject_id

    def compute_grade(self) -> GradeResult:
        self.total_obtained = self.cq_obtained + self.mcq_obtained + self.practical_obtained
        result = grade_for_marks(self.total_obtained, self.subject.total_marks)
        self.letter_grade = result.letter_grade
        self.grade_point = result.grade_point
        return result

    def save(self, *args, **kwargs):
        self.compute_grade()
        super().save(*args, **kwargs)


class ExamResult(TimeStampedModel):
    """
    One row per student per exam — the rolled-up final GPA, computed from
    that student's MarkEntry rows for the exam. Recompute with
    apps.exams.services.recompute_result(student, exam).
    """

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="results")
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    is_pass = models.BooleanField(default=False)

    class Meta:
        ordering = ["-exam__date"]
        unique_together = [("exam", "student")]

    def __str__(self):
        return f"{self.student} - {self.exam}: GPA {self.gpa}"
