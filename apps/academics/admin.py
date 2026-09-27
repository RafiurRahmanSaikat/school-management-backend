from django.contrib import admin

from .models import AcademicYear, Group, SchoolClass, Section, Subject


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("year", "is_current")
    list_filter = ("is_current",)
    ordering = ("-year",)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("level", "name")
    ordering = ("level",)
    search_fields = ("name",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        "school_class",
        "name",
        "group",
        "academic_year",
        "class_teacher",
        "capacity",
    )
    list_filter = ("academic_year", "school_class", "group")
    search_fields = ("name", "school_class__name")
    autocomplete_fields = ("class_teacher",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "category",
        "total_marks",
        "is_fourth_subject_candidate",
    )
    list_filter = ("category", "is_fourth_subject_candidate", "applicable_classes")
    search_fields = ("code", "name")
    filter_horizontal = ("applicable_classes",)
