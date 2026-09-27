from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "pin_to_top", "published_at", "published_by")
    list_filter = ("category", "is_published", "pin_to_top")
    search_fields = ("title", "body")
    autocomplete_fields = ("published_by",)

    def save_model(self, request, obj, form, change):
        if not obj.published_by_id:
            obj.published_by = request.user
        super().save_model(request, obj, form, change)
