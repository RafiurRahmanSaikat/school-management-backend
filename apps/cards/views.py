from django.http import FileResponse, Http404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.exams.models import Exam
from apps.students.services import filter_students

from .models import DocumentType, GeneratedDocument
from .serializers import GeneratedDocumentSerializer
from .services import (
    generate_admit_card,
    generate_id_card,
    generate_registration_card,
    generate_testimonial,
    save_generated_pdf,
)


def _describe_filters(request):
    """Human-readable summary of the query params used, for GeneratedDocument.filter_summary."""
    parts = []
    for label, key in [
        ("class", "class_id"),
        ("section", "section_id"),
        ("group", "group_id"),
        ("roll", "roll_start"),
        ("reg", "reg_start"),
    ]:
        value = request.query_params.get(key)
        if value:
            parts.append(f"{label}={value}")
    return ", ".join(parts) or "all accessible students"


class BaseCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get_students(self, request, student_id=None):
        try:
            return filter_students(
                request.user,
                student_id=student_id,
                class_id=request.query_params.get("class_id"),
                section_id=request.query_params.get("section_id"),
                group_id=request.query_params.get("group_id"),
                roll_start=request.query_params.get("roll_start"),
                roll_end=request.query_params.get("roll_end"),
                reg_start=request.query_params.get("reg_start"),
                reg_end=request.query_params.get("reg_end"),
            )
        except ValueError:
            raise Http404("No student(s) matched the given criteria.")

    def respond_with_pdf(
        self, request, buf, doc_type, students, filename, language="EN", exam=None
    ):
        # Persist a copy to MEDIA_ROOT before streaming it back, so it shows
        # up in the generated-documents history and can be re-downloaded
        # later without regenerating it.
        save_generated_pdf(
            buf,
            doc_type,
            students,
            user=request.user,
            language=language,
            exam=exam,
            filter_summary=_describe_filters(request),
        )
        buf.seek(0)
        return FileResponse(
            buf, as_attachment=False, filename=filename, content_type="application/pdf"
        )


class StudentIDCardView(BaseCardView):
    def get(self, request, student_id=None):
        students = self.get_students(request, student_id)
        buf = generate_id_card(students)
        filename = (
            "id_cards_bulk.pdf"
            if len(students) > 1
            else f"id_card_{students[0].registration_no}.pdf"
        )
        return self.respond_with_pdf(
            request, buf, DocumentType.ID_CARD, students, filename
        )


class StudentRegistrationCardView(BaseCardView):
    def get(self, request, student_id=None):
        students = self.get_students(request, student_id)
        buf = generate_registration_card(students)
        filename = (
            "registration_cards_bulk.pdf"
            if len(students) > 1
            else f"registration_card_{students[0].registration_no}.pdf"
        )
        return self.respond_with_pdf(
            request, buf, DocumentType.REGISTRATION_CARD, students, filename
        )


class StudentAdmitCardView(BaseCardView):
    def get(self, request, student_id=None, exam_id=None):
        exam_id = exam_id or request.query_params.get("exam_id")
        if not exam_id:
            raise Http404("Exam ID is required via path or query params.")

        exam = Exam.objects.filter(pk=exam_id).first()
        if not exam:
            raise Http404("Exam not found.")

        students = self.get_students(request, student_id)
        buf = generate_admit_card(students, exam)
        filename = (
            f"admit_cards_bulk_{exam.id}.pdf"
            if len(students) > 1
            else f"admit_card_{students[0].registration_no}_{exam.id}.pdf"
        )
        return self.respond_with_pdf(
            request, buf, DocumentType.ADMIT_CARD, students, filename, exam=exam
        )


class StudentTestimonialView(BaseCardView):
    """
    /api/cards/testimonial/<student_id>?language=EN|BN
    /api/cards/testimonial/bulk?class_id=&section_id=&group_id=&language=EN|BN
    """

    def get(self, request, student_id=None):
        language = request.query_params.get("language", "EN").upper()
        if language not in ("EN", "BN"):
            language = "EN"

        students = self.get_students(request, student_id)
        buf = generate_testimonial(students, language=language)
        suffix = "bn" if language == "BN" else "en"
        filename = (
            f"testimonials_bulk_{suffix}.pdf"
            if len(students) > 1
            else f"testimonial_{students[0].registration_no}_{suffix}.pdf"
        )
        return self.respond_with_pdf(
            request,
            buf,
            DocumentType.TESTIMONIAL,
            students,
            filename,
            language=language,
        )


class GeneratedDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only history of every generated card/testimonial batch, newest first."""

    queryset = GeneratedDocument.objects.select_related("generated_by", "exam")
    serializer_class = GeneratedDocumentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["doc_type", "language"]
