from django.db.models import Q

from .models import Student


def accessible_students_queryset(user):
    """
    admin/headteacher (or superuser): every student.
    class teacher: students in the section(s) they are class teacher of.
    other teacher: students in section(s) they are assigned to teach in
    (read-only access is enforced at the view/permission layer, not here).
    """
    qs = Student.objects.select_related(
        "section__school_class", "section__group", "optional_fourth_subject"
    )
    if user.is_superuser or user.is_admin_or_headteacher:
        return qs

    teacher_profile = getattr(user, "teacher_profile", None)
    if not teacher_profile:
        return qs.none()

    class_teacher_section_ids = list(
        teacher_profile.class_teacher_of_sections.values_list("id", flat=True)
    )
    subject_teacher_section_ids = list(
        teacher_profile.assigned_sections.values_list("id", flat=True)
    )
    return qs.filter(
        Q(section_id__in=class_teacher_section_ids)
        | Q(section_id__in=subject_teacher_section_ids)
    ).distinct()


def filter_students(
    user,
    student_id=None,
    class_id=None,
    section_id=None,
    group_id=None,
    roll_start=None,
    roll_end=None,
    reg_start=None,
    reg_end=None,
):
    """
    Single source of truth for "which students match these filters", used by
    both the card-generation API (apps.cards.views) and the card-generation
    Django frontend (apps.cards.frontend_views).

    NOTE (bug fix): Student has no `school_class` or `group` DB field of its
    own — those only exist as Python properties that proxy to
    `student.section.school_class` / `student.section.group`. Filtering the
    queryset therefore has to go through `section__school_class_id` /
    `section__group_id`, not `school_class_id` / `group_id` (which raised a
    FieldError / silently matched nothing before this fix).

    Returns a list of Student instances, ordered by roll number. Raises
    ValueError("no_match") if nothing matched, so callers (API view /
    Django view) can turn that into whatever 404/message makes sense for
    their layer.
    """
    queryset = accessible_students_queryset(user)

    if student_id is not None:
        student = queryset.filter(pk=student_id).first()
        if not student:
            raise ValueError("no_match")
        return [student]

    if class_id:
        queryset = queryset.filter(section__school_class_id=class_id)
    if section_id:
        queryset = queryset.filter(section_id=section_id)
    if group_id:
        queryset = queryset.filter(section__group_id=group_id)

    if roll_start and roll_end:
        queryset = queryset.filter(roll_no__range=(roll_start, roll_end))
    elif roll_start:
        queryset = queryset.filter(roll_no__gte=roll_start)

    if reg_start and reg_end:
        queryset = queryset.filter(registration_no__range=(reg_start, reg_end))
    elif reg_start:
        queryset = queryset.filter(registration_no__gte=reg_start)

    students = list(queryset.order_by("roll_no"))
    if not students:
        raise ValueError("no_match")

    return students


# from django.db.models import Q

# from .models import Student


# def accessible_students_queryset(user):
#     """
#     admin/headteacher (or superuser): every student.
#     class teacher: students in the section(s) they are class teacher of.
#     other teacher: students in section(s) they are assigned to teach in
#     (read-only access is enforced at the view/permission layer, not here).
#     """
#     qs = Student.objects.select_related(
#         "section__school_class", "section__group", "optional_fourth_subject"
#     )
#     if user.is_superuser or user.is_admin_or_headteacher:
#         return qs

#     teacher_profile = getattr(user, "teacher_profile", None)
#     if not teacher_profile:
#         return qs.none()

#     class_teacher_section_ids = list(teacher_profile.class_teacher_of_sections.values_list("id", flat=True))
#     subject_teacher_section_ids = list(teacher_profile.assigned_sections.values_list("id", flat=True))
#     return qs.filter(
#         Q(section_id__in=class_teacher_section_ids) | Q(section_id__in=subject_teacher_section_ids)
#     ).distinct()
