from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    This project's User is a custom AbstractUser subclass (see models.py), so
    the default `admin.site.register(User)` / plain ModelAdmin would show a
    raw password hash field and lose the "change password" form + permissions
    widgets. Subclassing Django's own UserAdmin keeps all of that and just
    adds this project's extra fields (role, phone, address, profile photo...).

    NOTE: if `AUTH_USER_MODEL` in settings.py is not set to "accounts.User",
    this admin (and login using this model) will not work — Django will
    still be using the default auth.User under the hood. Confirm in
    settings.py:  AUTH_USER_MODEL = "accounts.User"
    """

    model = User
    list_display = (
        "username",
        "full_name_display",
        "email",
        "role",
        "is_staff",
        "is_active",
        "is_active_staff",
    )
    list_filter = (
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
        "is_active_staff",
        "gender",
    )
    search_fields = ("username", "first_name", "last_name", "email", "phone")
    ordering = ("-date_joined",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "School profile",
            {
                "fields": (
                    "role",
                    "is_active_staff",
                    "phone",
                    "gender",
                    "date_of_birth",
                    "profile_picture",
                    "address_line",
                    "city",
                    "district",
                    "post_code",
                    "country",
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "School profile",
            {"classes": ("wide",), "fields": ("role", "email", "phone")},
        ),
    )

    @admin.display(description="Full name")
    def full_name_display(self, obj):
        return obj.get_full_name()


# --- Global admin branding -------------------------------------------------
# apps.accounts is always installed, so this is a convenient single place
# for it; move these three lines to config/urls.py (or a core AppConfig
# .ready()) instead if you'd rather keep branding out of an app's admin.py.
admin.site.site_header = "School Management System — Admin"
admin.site.site_title = "SMS Admin"
admin.site.index_title = "Administration"
