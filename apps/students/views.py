from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsClassTeacherOfStudentOrAbove

from .models import Student
from .serializers import StudentDetailSerializer, StudentListSerializer, StudentWriteSerializer
from .services import accessible_students_queryset


class StudentViewSet(viewsets.ModelViewSet):
    """
    Visibility rules:
      - admin / headteacher (or superuser): see & edit every student.
      - class teacher: full access to students in the section(s) they are
        the class teacher of.
      - any other teacher: read-only, limited to students in sections they
        are assigned to teach a subject in.
    Object-level write protection is additionally enforced by
    IsClassTeacherOfStudentOrAbove (a subject teacher can never edit, even if
    they can list/view).
    """

    permission_classes = [IsAuthenticated, IsClassTeacherOfStudentOrAbove]
    filterset_fields = ["section", "status", "gender", "section__school_class", "section__group"]
    search_fields = ["first_name", "last_name", "registration_no", "father_name", "mother_name"]

    def get_queryset(self):
        return accessible_students_queryset(self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return StudentListSerializer
        if self.action in ("create", "update", "partial_update"):
            return StudentWriteSerializer
        return StudentDetailSerializer
