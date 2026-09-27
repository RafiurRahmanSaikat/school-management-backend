from django.db import models

from apps.core.models import TimeStampedModel


class CommentVisibility(models.TextChoices):
    INTERNAL = "INTERNAL", "Staff only"
    GUARDIAN = "GUARDIAN", "Visible to guardian"


class TeacherComment(TimeStampedModel):
    """
    A remark a teacher leaves on a student's record — behavioural note,
    academic progress remark, exam feedback, etc. Kept as its own app (rather
    than a text field on Student) so a student can accumulate many comments
    over time from many different teachers without Student itself growing
    unbounded.
    """

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="comments")
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name="comments_made")
    exam = models.ForeignKey(
        "exams.Exam", on_delete=models.SET_NULL, null=True, blank=True, related_name="comments",
        help_text="Optional — link the comment to a specific exam/report card.",
    )
    comment = models.TextField()
    visibility = models.CharField(max_length=10, choices=CommentVisibility.choices, default=CommentVisibility.INTERNAL)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.teacher} on {self.student}: {self.comment[:40]}"
