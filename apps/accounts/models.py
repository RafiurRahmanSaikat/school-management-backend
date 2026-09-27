from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import PersonMixin, TimeStampedModel, UUIDModel


class Role(models.TextChoices):
    """
    Every account that can LOG IN falls into one of these roles.
    Students are intentionally NOT a role here — in v1 they are records
    managed by staff, not login accounts (see apps/students). Promoting a
    student to a portal login later is a matter of adding "STUDENT" here
    and a OneToOne on Student, without touching anything else.
    """

    ADMIN = "ADMIN", "Admin"
    HEADTEACHER = "HEADTEACHER", "Headteacher"
    TEACHER = "TEACHER", "Teacher"
    STAFF = "STAFF", "Staff"


class User(AbstractUser, PersonMixin, UUIDModel, TimeStampedModel):
    """
    Single source of truth for "name / email / profile pic / phone / address /
    gender" for every human who logs into the system. Teacher-specific data
    (designation, subjects, qualifications...) lives in apps.teachers.Teacher,
    linked one-to-one to this User — we don't repeat the shared fields there.
    """

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    is_active_staff = models.BooleanField(
        default=True,
        help_text="Soft flag for suspending an account without deleting it.",
    )

    # AbstractUser already gives us: username, first_name, last_name, email,
    # password, is_staff, is_active, is_superuser, date_joined, last_login.

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin_or_headteacher(self) -> bool:
        return self.is_superuser or self.role in (Role.ADMIN, Role.HEADTEACHER)
