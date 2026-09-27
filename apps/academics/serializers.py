from rest_framework import serializers

from .models import AcademicYear, Group, SchoolClass, Section, Subject


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ["id", "year", "is_current"]


class SchoolClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolClass
        fields = ["id", "level", "name"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name", "code"]


class SectionSerializer(serializers.ModelSerializer):
    school_class_name = serializers.CharField(source="school_class.name", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True, default=None)
    class_teacher_name = serializers.CharField(
        source="class_teacher.user.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Section
        fields = [
            "id", "academic_year", "school_class", "school_class_name", "name",
            "group", "group_name", "class_teacher", "class_teacher_name", "capacity",
        ]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id", "name", "code", "category", "total_marks", "cq_marks",
            "mcq_marks", "practical_marks", "is_fourth_subject_candidate",
            "applicable_classes",
        ]
