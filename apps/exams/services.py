from decimal import Decimal

from .grading import SubjectResult, calculate_gpa
from .models import Exam, ExamResult, MarkEntry


def recompute_result(student, exam: Exam) -> ExamResult:
    """
    Pulls every MarkEntry the student has for this exam, feeds them through
    the pure grading.calculate_gpa() function, and upserts the ExamResult row.
    Call this after marks for a student+exam are finalised (e.g. from a
    "publish results" admin action or automatically once every subject for
    that student/exam has a MarkEntry).
    """
    entries = MarkEntry.objects.filter(student=student, exam=exam).select_related("subject")

    subject_results = [
        SubjectResult(
            subject_code=e.subject.code,
            grade_point=e.grade_point,
            is_fourth_subject=e.is_fourth_subject,
        )
        for e in entries
    ]
    gpa = calculate_gpa(subject_results)

    result, _created = ExamResult.objects.update_or_create(
        exam=exam, student=student, defaults={"gpa": gpa, "is_pass": gpa > Decimal("0.00")}
    )
    return result
