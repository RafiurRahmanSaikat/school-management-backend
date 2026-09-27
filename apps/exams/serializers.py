from rest_framework import serializers

from .models import Exam, ExamResult, MarkEntry


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["id", "name", "exam_type", "academic_year", "school_class", "date"]


class MarkEntrySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)

    class Meta:
        model = MarkEntry
        fields = [
            "id", "exam", "student", "subject", "subject_name", "subject_code",
            "cq_obtained", "mcq_obtained", "practical_obtained",
            "total_obtained", "letter_grade", "grade_point", "entered_by",
        ]
        read_only_fields = ["total_obtained", "letter_grade", "grade_point"]


class ExamResultSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source="exam.name", read_only=True)

    class Meta:
        model = ExamResult
        fields = ["id", "exam", "exam_name", "student", "gpa", "is_pass"]
