from django.contrib import admin

from .models import Bill, FeeCategory, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("amount", "method", "paid_on", "received_by", "note")
    autocomplete_fields = ("received_by",)


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "title",
        "category",
        "amount_due",
        "amount_paid",
        "balance_display",
        "status",
        "due_date",
    )
    list_filter = ("status", "category", "academic_year")
    search_fields = (
        "title",
        "student__first_name",
        "student__last_name",
        "student__registration_no",
    )
    autocomplete_fields = ("student", "category")
    inlines = [PaymentInline]

    @admin.display(description="Balance")
    def balance_display(self, obj):
        return obj.balance


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("bill", "amount", "method", "paid_on", "received_by")
    list_filter = ("method",)
    search_fields = ("bill__title", "bill__student__registration_no")
    autocomplete_fields = ("bill", "received_by")
