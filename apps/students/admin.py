from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "registration_no", "full_name", "section", "roll_no", "gender",
        "father_name", "father_phone", "status",
    )
    list_filter = ("section__school_class", "section__group", "section__name", "status", "gender", "religion")
    search_fields = (
        "first_name", "last_name", "registration_no", "father_name",
        "mother_name", "father_phone", "mother_phone",
    )
    autocomplete_fields = ("section", "optional_fourth_subject")

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.full_name
