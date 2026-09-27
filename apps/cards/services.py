"""
Generates every PDF this app produces (ID Card, Registration Card, Admit
Card, Testimonial) via ReportLab, as BytesIO. `save_generated_pdf` then
persists a copy of that BytesIO to MEDIA_ROOT and records it as a
GeneratedDocument, so both the DRF card API and the Django frontend can
offer a "generated documents" history with download links instead of the
PDF only ever existing as a single HTTP response.

Bangla text (used by the Bangla testimonial and optionally the Bangla
labels on any other document) needs a Bangla-capable TTF registered with
ReportLab — Helvetica cannot render Bangla glyphs. Drop
NotoSansBengali-Regular.ttf (and, for bold text, NotoSansBengali-Bold.ttf)
into apps/cards/fonts/ and this module will pick them up automatically; if
the files aren't there, Bangla testimonials silently fall back to
Helvetica, which will render Bangla as boxes/blanks — so add the fonts
before relying on this in production.
"""

import io
import os

from django.core.files.base import ContentFile
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

CARD_WIDTH, CARD_HEIGHT = 86 * mm, 54 * mm

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

# --- Bangla font registration (best-effort) ---------------------------------
BN_REGULAR = "Helvetica"
BN_BOLD = "Helvetica-Bold"
_regular_path = os.path.join(FONTS_DIR, "NotoSansBengali-Regular.ttf")
_bold_path = os.path.join(FONTS_DIR, "NotoSansBengali-Bold.ttf")
if os.path.exists(_regular_path):
    pdfmetrics.registerFont(TTFont("NotoBengali", _regular_path))
    BN_REGULAR = "NotoBengali"
    BN_BOLD = "NotoBengali"  # overwritten below if a bold face is also present
if os.path.exists(_bold_path):
    pdfmetrics.registerFont(TTFont("NotoBengali-Bold", _bold_path))
    BN_BOLD = "NotoBengali-Bold"


def _draw_photo_box(c, x, y, w, h):
    c.setStrokeColor(colors.grey)
    c.rect(x, y, w, h)
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.grey)
    c.drawCentredString(x + w / 2, y + h / 2, "PHOTO")
    c.setFillColor(colors.black)


def _draw_single_id_card(c, student):
    """Helper to draw one ID card on the current canvas page."""
    c.setFillColor(colors.HexColor("#0f5132"))
    c.rect(0, CARD_HEIGHT - 10 * mm, CARD_WIDTH, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(CARD_WIDTH / 2, CARD_HEIGHT - 7 * mm, "STUDENT ID CARD")
    c.setFillColor(colors.black)

    _draw_photo_box(c, 4 * mm, 10 * mm, 20 * mm, 24 * mm)

    text_x = 27 * mm
    y = CARD_HEIGHT - 15 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, y, str(student.full_name)[:22])
    y -= 5 * mm
    c.setFont("Helvetica", 7.5)

    section_name = (
        student.section.name if hasattr(student, "section") and student.section else "-"
    )
    group_name = (
        student.group.name if hasattr(student, "group") and student.group else "-"
    )

    for label, value in [
        ("Class", f"{student.school_class} - {section_name}"),
        ("Group", group_name),
        ("Roll", str(student.roll_no)),
        ("Reg. No", str(student.registration_no)),
        ("Blood Grp", student.blood_group or "-"),
        ("Phone", student.phone or student.guardian_phone or "-"),
    ]:
        c.drawString(text_x, y, f"{label}: {value}")
        y -= 4 * mm

    c.setFont("Helvetica", 6)
    uuid_str = (
        student.uuid.hex[:12].upper()
        if hasattr(student, "uuid") and student.uuid
        else "-"
    )
    c.drawCentredString(CARD_WIDTH / 2, 3 * mm, f"ID: {uuid_str}")


def _draw_single_registration_card(c, student):
    """Helper to draw one Registration Card on an A5 canvas page."""
    width, height = A5
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 20 * mm, "STUDENT REGISTRATION CARD")
    c.line(15 * mm, height - 23 * mm, width - 15 * mm, height - 23 * mm)

    _draw_photo_box(c, width - 45 * mm, height - 70 * mm, 28 * mm, 35 * mm)

    section_name = (
        student.section.name if hasattr(student, "section") and student.section else "-"
    )
    group_name = (
        student.group.name if hasattr(student, "group") and student.group else "-"
    )

    rows = [
        ("Full Name", student.full_name),
        ("Registration No", student.registration_no),
        ("Date of Birth", str(student.date_of_birth or "-")),
        (
            "Gender",
            (
                student.get_gender_display()
                if hasattr(student, "get_gender_display") and student.gender
                else "-"
            ),
        ),
        (
            "Religion",
            (
                student.get_religion_display()
                if hasattr(student, "get_religion_display")
                else "-"
            ),
        ),
        ("Class / Section", f"{student.school_class} - {section_name}"),
        ("Group", group_name),
        ("Roll No", str(student.roll_no)),
        ("Previous School", getattr(student, "previous_school", "-")),
        ("Admission Date", str(getattr(student, "admission_date", "-"))),
        ("Father's Name", getattr(student, "father_name", "-")),
        ("Father's Phone", getattr(student, "father_phone", "-")),
        ("Mother's Name", getattr(student, "mother_name", "-")),
        ("Mother's Phone", getattr(student, "mother_phone", "-")),
        ("Address", getattr(student, "full_address", "-")),
    ]

    y = height - 35 * mm
    for label, value in rows:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(15 * mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(55 * mm, y, str(value)[:45])
        y -= 7 * mm

    c.setFont("Helvetica", 8)
    c.drawString(15 * mm, 15 * mm, "Signature of Guardian: ______________________")
    c.drawString(15 * mm, 8 * mm, "Signature of Headteacher: ______________________")


def _draw_single_admit_card(c, student, exam):
    """Helper to draw one Admit Card on an A5 canvas page."""
    width, height = A5
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 18 * mm, "ADMIT CARD")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 25 * mm, exam.name)
    c.line(15 * mm, height - 28 * mm, width - 15 * mm, height - 28 * mm)

    _draw_photo_box(c, width - 45 * mm, height - 70 * mm, 28 * mm, 35 * mm)

    section_name = (
        student.section.name if hasattr(student, "section") and student.section else "-"
    )
    group_name = (
        student.group.name if hasattr(student, "group") and student.group else "-"
    )

    rows = [
        ("Student Name", student.full_name),
        ("Registration No", student.registration_no),
        ("Roll No", str(student.roll_no)),
        ("Class / Section", f"{student.school_class} - {section_name}"),
        ("Group", group_name),
        (
            "Exam",
            (
                exam.get_exam_type_display()
                if hasattr(exam, "get_exam_type_display")
                else str(exam.name)
            ),
        ),
        ("Exam Date", str(exam.date)),
    ]

    y = height - 40 * mm
    for label, value in rows:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(15 * mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(55 * mm, y, str(value)[:45])
        y -= 7 * mm

    subjects = student.school_class.subjects.all().order_by("code")
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(15 * mm, y, "Subjects:")
    y -= 6 * mm
    c.setFont("Helvetica", 8)
    for subj in subjects:
        c.drawString(20 * mm, y, f"{subj.code} - {subj.name}")
        y -= 5 * mm

    c.setFont("Helvetica", 8)
    c.drawString(15 * mm, 12 * mm, "Signature of Student: ______________________")
    c.drawString(15 * mm, 6 * mm, "Signature of Headteacher: ______________________")


def _testimonial_text(student, language):
    """Returns (title, body_lines, footer_lines) for the given language."""
    section_name = student.section.name if student.section else "-"
    group_name = student.group.name if student.group else "General"
    admission_date = getattr(student, "admission_date", None)
    today = timezone.localdate()

    if language == "BN":
        gender_word = "তিনি" if student.gender != "F" else "সে"
        title = "প্রশংসাপত্র"
        body_lines = [
            f"এই মর্মে প্রত্যয়ন করা যাচ্ছে যে, {student.full_name}, পিতা: "
            f"{student.father_name or '-'}, মাতা: {student.mother_name or '-'},",
            f"রেজিস্ট্রেশন নং {student.registration_no}, {student.school_class} শ্রেণীর "
            f"'{section_name}' শাখার একজন নিয়মিত ছাত্র/ছাত্রী।",
            f"শ্রেণি বিভাগ: {group_name}    রোল নং: {student.roll_no}",
            (
                f"তিনি {admission_date:%d/%m/%Y} তারিখে এই বিদ্যালয়ে ভর্তি হন।"
                if admission_date
                else "ভর্তির তারিখ বিদ্যালয়ের রেকর্ডে সংরক্ষিত আছে।"
            ),
            "বিদ্যালয়ে অধ্যয়নকালীন সময়ে তার চরিত্র ও আচরণ সন্তোষজনক ছিল।",
            "আমরা তার সার্বিক মঙ্গল ও উজ্জ্বল ভবিষ্যৎ কামনা করি।",
        ]
        footer_lines = [f"প্রদানের তারিখ: {today:%d/%m/%Y}"]
    else:
        title = "TESTIMONIAL"
        body_lines = [
            f"This is to certify that {student.full_name}, son/daughter of "
            f"{student.father_name or '-'} and {student.mother_name or '-'},",
            f"bearing Registration No. {student.registration_no}, was a bona-fide "
            f"student of {student.school_class}, Section '{section_name}'",
            f"(Group: {group_name}, Roll No. {student.roll_no}) of this institution.",
            (
                f"He/She was admitted to this school on {admission_date:%d %B, %Y}."
                if admission_date
                else "The date of admission is on record with the school."
            ),
            "During his/her stay in this institution, his/her conduct and character "
            "were found to be satisfactory.",
            "We wish him/her every success in future endeavours.",
        ]
        footer_lines = [f"Date of Issue: {today:%d %B, %Y}"]

    return title, body_lines, footer_lines


def _draw_single_testimonial(c, student, language="EN"):
    """Draws one A4 testimonial/certificate page, in English or Bangla."""
    width, height = A4
    regular = BN_REGULAR if language == "BN" else "Helvetica"
    bold = BN_BOLD if language == "BN" else "Helvetica-Bold"

    # Decorative border
    c.setStrokeColor(colors.HexColor("#0f5132"))
    c.setLineWidth(2)
    c.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm)

    title, body_lines, footer_lines = _testimonial_text(student, language)

    c.setFont(bold, 20)
    c.setFillColor(colors.HexColor("#0f5132"))
    c.drawCentredString(width / 2, height - 35 * mm, title)
    c.setFillColor(colors.black)
    c.line(width / 2 - 30 * mm, height - 40 * mm, width / 2 + 30 * mm, height - 40 * mm)

    y = height - 65 * mm
    c.setFont(regular, 12)
    max_width = width - 50 * mm
    for line in body_lines:
        for wrapped in _wrap_text(c, line, regular, 12, max_width):
            c.drawString(25 * mm, y, wrapped)
            y -= 8 * mm
        y -= 4 * mm

    y -= 15 * mm
    c.setFont(regular, 10)
    for line in footer_lines:
        c.drawString(25 * mm, y, line)
        y -= 6 * mm

    sig_label = "প্রধান শিক্ষকের স্বাক্ষর" if language == "BN" else "Signature of Headteacher"
    c.setFont(regular, 10)
    c.drawString(width - 75 * mm, 30 * mm, "______________________")
    c.drawString(width - 75 * mm, 24 * mm, sig_label)


def _wrap_text(c, text, font_name, font_size, max_width):
    """Naive word-wrap so long testimonial lines don't run off the A4 page."""
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if c.stringWidth(candidate, font_name, font_size) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# Public Generators ------------------------------------------------------


def generate_id_card(students) -> io.BytesIO:
    """Generates ID cards for a single student or a list/queryset of students."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(CARD_WIDTH, CARD_HEIGHT))
    student_list = [students] if not hasattr(students, "__iter__") else list(students)

    for student in student_list:
        _draw_single_id_card(c, student)
        c.showPage()

    c.save()
    buf.seek(0)
    return buf


def generate_registration_card(students) -> io.BytesIO:
    """Generates Registration cards for a single student or a list/queryset of students."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A5)
    student_list = [students] if not hasattr(students, "__iter__") else list(students)

    for student in student_list:
        _draw_single_registration_card(c, student)
        c.showPage()

    c.save()
    buf.seek(0)
    return buf


def generate_admit_card(students, exam) -> io.BytesIO:
    """Generates Admit cards for a single student or a list/queryset of students."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A5)
    student_list = [students] if not hasattr(students, "__iter__") else list(students)

    for student in student_list:
        _draw_single_admit_card(c, student, exam)
        c.showPage()

    c.save()
    buf.seek(0)
    return buf


def generate_testimonial(students, language="EN") -> io.BytesIO:
    """
    Generates one A4 testimonial/certificate per student (single student or
    bulk), in English ("EN") or Bangla ("BN").
    """
    language = "BN" if str(language).upper() == "BN" else "EN"
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    student_list = [students] if not hasattr(students, "__iter__") else list(students)

    for student in student_list:
        _draw_single_testimonial(c, student, language)
        c.showPage()

    c.save()
    buf.seek(0)
    return buf


# Persistence helper ------------------------------------------------------


def save_generated_pdf(buf, doc_type, students, user=None, language="EN", exam=None, filter_summary=""):
    """
    Saves a copy of an already-generated PDF (`buf`, a BytesIO as returned by
    the generate_* functions above) into MEDIA_ROOT and records it as a
    GeneratedDocument, so it shows up in the "generated documents" history
    and can be re-downloaded later without regenerating it.

    Returns the created GeneratedDocument. Does NOT consume/close `buf` —
    callers can still stream the same bytes back in the HTTP response.
    """
    from .models import DocumentLanguage, DocumentType, GeneratedDocument  # local import: avoids AppRegistryNotReady at import time

    data = buf.getvalue()
    doc = GeneratedDocument(
        doc_type=doc_type,
        language=language if doc_type == DocumentType.TESTIMONIAL else DocumentLanguage.EN,
        student_count=len(students),
        filter_summary=filter_summary,
        exam=exam,
        generated_by=user if (user and getattr(user, "is_authenticated", False)) else None,
    )
    # doc_type-specific filename so the media folder stays browsable on its own
    slug = doc_type.lower()
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{slug}_{stamp}_{len(students)}.pdf"
    doc.file.save(filename, ContentFile(data), save=False)
    doc.save()
    return doc
