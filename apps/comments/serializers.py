from rest_framework import serializers

from .models import TeacherComment


class TeacherCommentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)

    class Meta:
        model = TeacherComment
        fields = ["id", "student", "teacher", "teacher_name", "exam", "comment", "visibility", "created_at"]
        read_only_fields = ["teacher"]
