from django.contrib import admin

from .models import TeacherComment


@admin.register(TeacherComment)
class TeacherCommentAdmin(admin.ModelAdmin):
    list_display = ("student", "teacher", "exam", "visibility", "created_at")
    list_filter = ("visibility", "exam")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__registration_no",
        "teacher__employee_id",
        "comment",
    )
    autocomplete_fields = ("student", "teacher", "exam")
