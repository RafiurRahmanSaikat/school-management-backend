from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id", "full_name", "designation", "phone", "joining_date", "is_active_employee",
    )
    list_filter = ("designation", "is_active_employee")
    search_fields = ("employee_id", "user__first_name", "user__last_name", "user__email")
    filter_horizontal = ("subjects", "assigned_sections")
    autocomplete_fields = ("user",)

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.user.get_full_name()

    @admin.display(description="Phone")
    def phone(self, obj):
        return obj.user.phone
