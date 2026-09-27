from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsTeacherOrAbove

from .models import TeacherComment
from .serializers import TeacherCommentSerializer


class TeacherCommentViewSet(viewsets.ModelViewSet):
    queryset = TeacherComment.objects.select_related("student", "teacher__user", "exam")
    serializer_class = TeacherCommentSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAbove]
    filterset_fields = ["student", "teacher", "exam", "visibility"]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or user.is_admin_or_headteacher:
            return qs
        teacher_profile = getattr(user, "teacher_profile", None)
        if not teacher_profile:
            return qs.none()
        allowed_sections = list(teacher_profile.assigned_sections.values_list("id", flat=True)) + list(
            teacher_profile.class_teacher_of_sections.values_list("id", flat=True)
        )
        return qs.filter(student__section_id__in=allowed_sections)

    def perform_create(self, serializer):
        teacher_profile = getattr(self.request.user, "teacher_profile", None)
        serializer.save(teacher=teacher_profile)
