"""
Core abstractions shared by every other app.

Keeping these here means "name / address / phone / gender / profile picture"
style fields are written ONCE and reused everywhere (User, Student, Teacher, ...)
instead of being copy-pasted app to app. Add a new shared field here and every
model that inherits the mixin gets it automatically.
"""
import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at to any model that inherits it."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Adds a public-facing UUID (safe to expose in URLs / QR codes on ID cards)."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class Gender(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    OTHER = "O", "Other"


class BloodGroup(models.TextChoices):
    A_POS = "A+", "A+"
    A_NEG = "A-", "A-"
    B_POS = "B+", "B+"
    B_NEG = "B-", "B-"
    AB_POS = "AB+", "AB+"
    AB_NEG = "AB-", "AB-"
    O_POS = "O+", "O+"
    O_NEG = "O-", "O-"
    UNKNOWN = "", "Unknown"


class PersonMixin(models.Model):
    """
    Shared "person" fields. Every human in the system (system user account,
    student record, teacher record, guardian) reuses this instead of each app
    redefining name/contact/address/gender/photo fields on its own.

    NOTE: apps.accounts.User already carries these for anyone who has a LOGIN
    account (admin, headteacher, teacher, staff). Student re-declares a subset
    directly (see apps/students/models.py) because a student typically does not
    get a login account of their own in v1, so it can't simply inherit User.
    """

    phone = models.CharField(max_length=20, blank=True)
    address_line = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    post_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="Bangladesh", blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def full_address(self) -> str:
        parts = [self.address_line, self.city, self.district, self.post_code, self.country]
        return ", ".join(p for p in parts if p)


class SocialLinksMixin(models.Model):
    """Optional social / online presence links — used mainly by Teacher profiles."""

    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    class Meta:
        abstract = True
