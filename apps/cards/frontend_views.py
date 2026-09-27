from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from apps.students.services import filter_students

from .forms import CardGenerationForm
from .models import DocumentType, GeneratedDocument
from .services import (
    generate_admit_card,
    generate_id_card,
    generate_registration_card,
    generate_testimonial,
    save_generated_pdf,
)

GENERATORS = {
    DocumentType.ID_CARD: lambda students, form: generate_id_card(students),
    DocumentType.REGISTRATION_CARD: lambda students, form: generate_registration_card(students),
    DocumentType.ADMIT_CARD: lambda students, form: generate_admit_card(students, form.cleaned_data["exam"]),
    DocumentType.TESTIMONIAL: lambda students, form: generate_testimonial(
        students, language=form.cleaned_data.get("language") or "EN"
    ),
}


def _describe_scope(form):
    """Human-readable filter summary for GeneratedDocument.filter_summary, e.g. 'Class 10 - Section A - Science'."""
    cd = form.cleaned_data
    parts = []
    if cd.get("school_class"):
        parts.append(str(cd["school_class"]))
    if cd.get("section"):
        parts.append(f"Section {cd['section'].name}")
    if cd.get("group"):
        parts.append(cd["group"].name)
    if cd.get("roll_start"):
        parts.append(f"Roll {cd['roll_start']}-{cd.get('roll_end') or cd['roll_start']}")
    if cd.get("reg_start"):
        parts.append(f"Reg {cd['reg_start']}-{cd.get('reg_end') or cd['reg_start']}")
    return " - ".join(parts) if parts else "All accessible students"


class CardGeneratorView(LoginRequiredMixin, View):
    """
    One page to generate ID / Registration / Admit cards or Testimonials
    (English or Bangla) for a single student or in bulk — by class only
    ("all of Class 10"), class + section ("Class 6 - Section A"), or
    class + section + group ("Class 10 - Section A - Science") — and have
    the resulting PDF saved to the media folder automatically.
    """

    template_name = "cards/generate.html"

    def get(self, request):
        form = CardGenerationForm()
        context = {"form": form}
        generated_id = request.GET.get("generated")
        if generated_id:
            context["generated_doc"] = GeneratedDocument.objects.filter(pk=generated_id).first()
        return render(request, self.template_name, context)

    def post(self, request):
        form = CardGenerationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        cd = form.cleaned_data
        try:
            students = filter_students(
                request.user,
                class_id=cd["school_class"].id if cd.get("school_class") else None,
                section_id=cd["section"].id if cd.get("section") else None,
                group_id=cd["group"].id if cd.get("group") else None,
                roll_start=cd.get("roll_start"),
                roll_end=cd.get("roll_end"),
                reg_start=cd.get("reg_start"),
                reg_end=cd.get("reg_end"),
            )
        except ValueError:
            form.add_error(None, "No students matched those filters.")
            return render(request, self.template_name, {"form": form})

        doc_type = cd["doc_type"]
        buf = GENERATORS[doc_type](students, form)
        doc = save_generated_pdf(
            buf, doc_type, students,
            user=request.user,
            language=cd.get("language") or "EN",
            exam=cd.get("exam"),
            filter_summary=_describe_scope(form),
        )
        # Redirect-after-POST so refreshing the result page doesn't regenerate the batch.
        return redirect(f"{reverse('cards-frontend:generate')}?generated={doc.pk}")


class GeneratedDocumentListView(LoginRequiredMixin, ListView):
    """History of every previously generated card/testimonial batch, with download links."""

    model = GeneratedDocument
    template_name = "cards/history.html"
    context_object_name = "documents"
    paginate_by = 25

    def get_queryset(self):
        qs = GeneratedDocument.objects.select_related("generated_by", "exam")
        doc_type = self.request.GET.get("doc_type")
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["doc_types"] = DocumentType.choices
        context["selected_doc_type"] = self.request.GET.get("doc_type", "")
        return context


class GeneratedDocumentDetailView(LoginRequiredMixin, DetailView):
    model = GeneratedDocument
    template_name = "cards/document_detail.html"
    context_object_name = "document"
