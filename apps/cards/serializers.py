from rest_framework import serializers

from .models import GeneratedDocument


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(
        source="generated_by.get_full_name", read_only=True, default=None
    )
    exam_name = serializers.CharField(source="exam.name", read_only=True, default=None)

    class Meta:
        model = GeneratedDocument
        fields = [
            "id", "doc_type", "language", "file", "student_count",
            "filter_summary", "exam", "exam_name", "generated_by",
            "generated_by_name", "created_at",
        ]
        read_only_fields = fields
