from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsAdminOrReadOnly

from .models import Teacher
from .serializers import TeacherSerializer, TeacherWriteSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    """
    Admin/headteacher: full CRUD over every teacher.
    Any authenticated user (teachers included) can read the directory.
    """

    queryset = Teacher.objects.select_related("user").prefetch_related(
        "subjects", "assigned_sections"
    )
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ["designation", "is_active_employee"]
    search_fields = ["employee_id", "user__first_name", "user__last_name"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TeacherWriteSerializer
        return TeacherSerializer
