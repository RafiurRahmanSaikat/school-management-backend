from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrReadOnly, IsTeacherOrAbove

from .models import Exam, ExamResult, MarkEntry
from .serializers import ExamResultSerializer, ExamSerializer, MarkEntrySerializer
from .services import recompute_result


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.select_related("school_class", "academic_year")
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ["exam_type", "school_class", "academic_year"]


class MarkEntryViewSet(viewsets.ModelViewSet):
    """
    Admin/headteacher: can enter/edit marks for anything.
    Teacher: can only enter/edit marks for subjects+sections they are
    assigned to teach (enforced in get_queryset; combined with the subject
    teacher only ever operating through this endpoint, not direct SQL).
    """

    queryset = MarkEntry.objects.select_related("student", "subject", "exam")
    serializer_class = MarkEntrySerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAbove]
    filterset_fields = ["exam", "student", "subject"]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or user.is_admin_or_headteacher:
            return qs
        teacher_profile = getattr(user, "teacher_profile", None)
        if not teacher_profile:
            return qs.none()
        return qs.filter(
            subject__in=teacher_profile.subjects.all(),
            student__section__in=teacher_profile.assigned_sections.all(),
        )

    def perform_create(self, serializer):
        teacher_profile = getattr(self.request.user, "teacher_profile", None)
        serializer.save(entered_by=teacher_profile)

    @action(detail=False, methods=["post"], url_path="recompute")
    def recompute(self, request):
        """POST {student: <id>, exam: <id>} -> recomputes and returns the ExamResult."""
        student_id = request.data.get("student")
        exam_id = request.data.get("exam")
        from apps.students.models import Student

        student = Student.objects.get(pk=student_id)
        exam = Exam.objects.get(pk=exam_id)
        result = recompute_result(student, exam)
        return Response(ExamResultSerializer(result).data)


class ExamResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExamResult.objects.select_related("student", "exam")
    serializer_class = ExamResultSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["exam", "student", "is_pass"]

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
