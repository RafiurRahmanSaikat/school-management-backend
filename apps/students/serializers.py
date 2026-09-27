from rest_framework import serializers

from .models import Student


class StudentListSerializer(serializers.ModelSerializer):
    """Light-weight — used for list views / search results / roll sheets."""

    full_name = serializers.CharField(read_only=True)
    class_name = serializers.CharField(source="section.school_class.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    group_name = serializers.CharField(source="section.group.name", read_only=True, default=None)

    class Meta:
        model = Student
        fields = [
            "id", "uuid", "registration_no", "roll_no", "full_name", "gender",
            "section", "class_name", "section_name", "group_name", "status",
            "profile_picture",
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    """
    Full record: admin / headteacher / class teacher view. Pulls together
    everything scattered across other apps (marks, bills, comments) so the
    frontend gets "the whole student" in one call.
    """

    full_name = serializers.CharField(read_only=True)
    class_name = serializers.CharField(source="section.school_class.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    group_name = serializers.CharField(source="section.group.name", read_only=True, default=None)
    total_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    latest_results = serializers.SerializerMethodField()
    teacher_comments = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id", "uuid", "first_name", "last_name", "full_name", "gender",
            "date_of_birth", "blood_group", "religion", "profile_picture",
            "phone", "address_line", "city", "district", "post_code", "country",
            "section", "class_name", "section_name", "group_name", "roll_no",
            "registration_no", "optional_fourth_subject", "admission_date",
            "previous_school", "status",
            "father_name", "father_phone", "father_occupation",
            "mother_name", "mother_phone", "mother_occupation",
            "guardian_relation", "guardian_name", "guardian_phone",
            "total_due", "latest_results", "teacher_comments",
        ]

    def get_latest_results(self, obj):
        from apps.exams.serializers import ExamResultSerializer

        results = obj.results.select_related("exam").order_by("-exam__date")[:5]
        return ExamResultSerializer(results, many=True).data

    def get_teacher_comments(self, obj):
        from apps.comments.serializers import TeacherCommentSerializer

        comments = obj.comments.select_related("teacher__user").order_by("-created_at")[:10]
        return TeacherCommentSerializer(comments, many=True).data


class StudentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "first_name", "last_name", "gender", "date_of_birth", "blood_group",
            "religion", "profile_picture", "phone", "address_line", "city",
            "district", "post_code", "country", "section", "roll_no",
            "registration_no", "optional_fourth_subject", "admission_date",
            "previous_school", "status", "father_name", "father_phone",
            "father_occupation", "mother_name", "mother_phone", "mother_occupation",
            "guardian_relation", "guardian_name", "guardian_phone",
        ]
