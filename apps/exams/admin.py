from django.contrib import admin

from .models import Exam, ExamResult, MarkEntry
from .services import recompute_result


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "exam_type", "school_class", "academic_year", "date")
    list_filter = ("exam_type", "school_class", "academic_year")
    search_fields = ("name",)


@admin.register(MarkEntry)
class MarkEntryAdmin(admin.ModelAdmin):
    list_display = (
        "student", "subject", "exam", "total_obtained", "letter_grade", "grade_point",
    )
    list_filter = ("exam", "subject")
    search_fields = ("student__first_name", "student__last_name", "student__registration_no")
    autocomplete_fields = ("student", "subject", "exam", "entered_by")
    actions = ["recompute_student_results"]

    @admin.action(description="Recompute GPA/result for the selected mark entries' students")
    def recompute_student_results(self, request, queryset):
        pairs = {(m.student_id, m.exam_id) for m in queryset}
        for student_id, exam_id in pairs:
            entry = queryset.filter(student_id=student_id, exam_id=exam_id).first()
            recompute_result(entry.student, entry.exam)
        self.message_user(request, f"Recomputed {len(pairs)} student result(s).")


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "gpa", "is_pass")
    list_filter = ("exam", "is_pass")
    search_fields = ("student__first_name", "student__last_name", "student__registration_no")
