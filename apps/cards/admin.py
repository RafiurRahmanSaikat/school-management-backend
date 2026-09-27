from django.contrib import admin

from .models import GeneratedDocument


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "doc_type", "language", "student_count", "filter_summary",
        "generated_by", "created_at",
    )
    list_filter = ("doc_type", "language")
    search_fields = ("filter_summary", "generated_by__username", "generated_by__email")
    readonly_fields = ("created_at", "updated_at")
