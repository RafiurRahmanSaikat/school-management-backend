"""
Central place for "who is allowed to do what".

Every app imports from here instead of re-writing role checks, so tightening
or loosening a rule (e.g. "can class teachers edit bills?") is a one-line
change in one file rather than a hunt through every app's views.py.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def _role(user):
    return getattr(user, "role", None)


class IsAdmin(BasePermission):
    """Full-control accounts: superadmin / admin / headteacher."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or _role(request.user) in ("ADMIN", "HEADTEACHER"))
        )


class IsAdminOrHeadteacher(IsAdmin):
    """Alias kept for readability at call sites."""


class IsAdminOrReadOnly(BasePermission):
    """Anyone authenticated can read; only admin/headteacher can write."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_superuser or _role(request.user) in ("ADMIN", "HEADTEACHER")


class IsTeacherOrAbove(BasePermission):
    """Admin, headteacher, or any teacher (including class teachers)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or _role(request.user) in ("ADMIN", "HEADTEACHER", "TEACHER")
            )
        )


class IsClassTeacherOfStudentOrAbove(BasePermission):
    """
    Admin/headteacher: full access to every student.
    A class teacher: full access only to students in the class+section they
    are the class teacher of. A regular subject teacher: read-only, and only
    for students they actually teach a subject to (handled at queryset level
    in the view — this permission just gates write access).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or _role(user) in ("ADMIN", "HEADTEACHER"):
            return True

        # obj is expected to be a Student instance (or expose .student)
        student = getattr(obj, "student", obj)

        teacher_profile = getattr(user, "teacher_profile", None)
        if not teacher_profile:
            return False

        is_class_teacher_of_this_student = teacher_profile.is_class_teacher_of(student.section_id)
        if request.method in SAFE_METHODS:
            # any teacher who teaches this student's class/section may view
            teaches_this_class = teacher_profile.assigned_sections.filter(
                pk=student.section_id
            ).exists()
            return is_class_teacher_of_this_student or teaches_this_class

        return is_class_teacher_of_this_student
