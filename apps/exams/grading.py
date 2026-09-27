"""
NCTB SSC grading & GPA rules — kept as pure functions (no DB / model
dependency) so they're trivial to unit test and to reuse (e.g. from a
management command or a report generator) without touching the ORM.

Grading scale (5.00 point scale):
    80-100  A+   5.00
    70-79   A    4.00
    60-69   A-   3.50
    50-59   B    3.00
    40-49   C    2.00
    33-39   D    1.00
    0-32    F    0.00

GPA rules:
    - If the grade point of ANY core (non-4th-subject) subject is 0.00 (F),
      the overall GPA is 0.00 — one failed core subject fails the whole year.
    - 4th subject bonus = 4th subject's grade point - 2.00 (floored at 0).
    - Final GPA = (sum of core subject grade points + 4th subject bonus)
                  / number of core subjects, capped at 5.00.
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

GRADE_SCALE = [
    (80, 100, "A+", Decimal("5.00")),
    (70, 79, "A", Decimal("4.00")),
    (60, 69, "A-", Decimal("3.50")),
    (50, 59, "B", Decimal("3.00")),
    (40, 49, "C", Decimal("2.00")),
    (33, 39, "D", Decimal("1.00")),
    (0, 32, "F", Decimal("0.00")),
]


@dataclass
class GradeResult:
    letter_grade: str
    grade_point: Decimal


def grade_for_marks(marks_obtained, total_marks) -> GradeResult:
    """
    Marks are first normalised to a /100 percentage (subjects like ICT are out
    of 50, not 100) before looking the grade up in the standard 100-mark scale.
    """
    if total_marks <= 0:
        raise ValueError("total_marks must be positive")
    percentage = (Decimal(marks_obtained) / Decimal(total_marks)) * Decimal(100)
    percentage = percentage.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    for low, high, letter, gp in GRADE_SCALE:
        if low <= percentage <= high:
            return GradeResult(letter_grade=letter, grade_point=gp)
    return GradeResult(letter_grade="F", grade_point=Decimal("0.00"))


@dataclass
class SubjectResult:
    subject_code: str
    grade_point: Decimal
    is_fourth_subject: bool = False


def calculate_gpa(subject_results: list[SubjectResult]) -> Decimal:
    """
    subject_results must include every subject the student sat for that exam,
    with is_fourth_subject=True on exactly the one subject that is their
    chosen optional 4th subject (if any).
    """
    core = [r for r in subject_results if not r.is_fourth_subject]
    fourth = next((r for r in subject_results if r.is_fourth_subject), None)

    if not core:
        return Decimal("0.00")

    if any(r.grade_point == Decimal("0.00") for r in core):
        return Decimal("0.00")

    core_sum = sum((r.grade_point for r in core), Decimal("0.00"))
    bonus = Decimal("0.00")
    if fourth is not None:
        bonus = max(fourth.grade_point - Decimal("2.00"), Decimal("0.00"))

    gpa = (core_sum + bonus) / Decimal(len(core))
    gpa = min(gpa, Decimal("5.00"))
    return gpa.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
