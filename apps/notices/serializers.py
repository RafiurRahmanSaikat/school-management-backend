from rest_framework import serializers

from .models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    published_by_name = serializers.CharField(source="published_by.get_full_name", read_only=True, default=None)

    class Meta:
        model = Notice
        fields = [
            "id", "title", "body", "category", "attachment", "is_published",
            "published_at", "published_by", "published_by_name", "pin_to_top",
        ]
        read_only_fields = ["published_by"]
