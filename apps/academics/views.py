from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsAdminOrReadOnly

from .models import AcademicYear, Group, SchoolClass, Section, Subject
from .serializers import (
    AcademicYearSerializer,
    GroupSerializer,
    SchoolClassSerializer,
    SectionSerializer,
    SubjectSerializer,
)


class BaseAcademicsViewSet(viewsets.ModelViewSet):
    """Read-only for everyone logged in, write access is admin/headteacher only."""

    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class AcademicYearViewSet(BaseAcademicsViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer


class SchoolClassViewSet(BaseAcademicsViewSet):
    queryset = SchoolClass.objects.all()
    serializer_class = SchoolClassSerializer


class GroupViewSet(BaseAcademicsViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class SectionViewSet(BaseAcademicsViewSet):
    queryset = Section.objects.select_related(
        "school_class", "group", "class_teacher__user"
    )
    serializer_class = SectionSerializer
    filterset_fields = ["academic_year", "school_class", "group"]


class SubjectViewSet(BaseAcademicsViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filterset_fields = ["category", "is_fourth_subject_candidate"]
