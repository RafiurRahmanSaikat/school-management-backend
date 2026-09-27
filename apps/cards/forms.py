from django import forms

from apps.academics.models import Group, SchoolClass, Section
from apps.exams.models import Exam

from .models import DocumentType


class CardGenerationForm(forms.Form):
    doc_type = forms.ChoiceField(choices=DocumentType.choices, label="Document type")

    # Scope: leave school_class blank + everything else blank to mean
    # "every student this account can see". Pick school_class alone for
    # "all of Class 10". Add section for "Class 10 - Section A". Add group
    # on top of that for "Class 10 - Section A - Science" (matches only if
    # that section's group is Science).
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(), required=False, label="Class",
        help_text="Leave blank to include every class.",
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.select_related("school_class", "group"),
        required=False, label="Section",
        help_text="Leave blank to include every section of the chosen class.",
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(), required=False, label="Group",
        help_text="Optional extra filter, e.g. Science/Commerce/Arts.",
    )

    roll_start = forms.IntegerField(required=False, label="Roll no. from")
    roll_end = forms.IntegerField(required=False, label="Roll no. to")
    reg_start = forms.CharField(required=False, label="Registration no. from")
    reg_end = forms.CharField(required=False, label="Registration no. to")

    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(), required=False, label="Exam",
        help_text="Required only when generating Admit Cards.",
    )
    language = forms.ChoiceField(
        choices=[("EN", "English"), ("BN", "Bangla")], required=False, initial="EN",
        label="Language", help_text="Only used for Testimonials.",
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("doc_type") == DocumentType.ADMIT_CARD and not cleaned.get("exam"):
            self.add_error("exam", "Select an exam to generate admit cards.")
        return cleaned
