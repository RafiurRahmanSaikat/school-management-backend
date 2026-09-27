from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Teacher


class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_class_teacher = serializers.BooleanField(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id", "user", "employee_id", "designation", "subjects",
            "assigned_sections", "education_qualification", "joining_date",
            "is_active_employee", "is_class_teacher",
            "facebook_url", "linkedin_url", "website_url",
        ]


class TeacherWriteSerializer(serializers.ModelSerializer):
    """Used for create/update where `user` is passed as an existing user id."""

    class Meta:
        model = Teacher
        fields = [
            "id", "user", "employee_id", "designation", "subjects",
            "assigned_sections", "education_qualification", "joining_date",
            "is_active_employee", "facebook_url", "linkedin_url", "website_url",
        ]
