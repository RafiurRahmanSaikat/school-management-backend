from decimal import Decimal

from django.db import models

from apps.core.models import TimeStampedModel


class FeeCategory(TimeStampedModel):
    """e.g. Tuition Fee, Admission Fee, Exam Fee, Session Fee, Transport Fee."""

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "Fee categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BillStatus(models.TextChoices):
    UNPAID = "UNPAID", "Unpaid"
    PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
    PAID = "PAID", "Paid"
    WAIVED = "WAIVED", "Waived"


class Bill(TimeStampedModel):
    """One due bill for a student (e.g. 'January 2026 Tuition Fee')."""

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="bills")
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name="bills")
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.CASCADE, related_name="bills")
    title = models.CharField(max_length=150, help_text="e.g. 'January 2026 Tuition Fee'")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=BillStatus.choices, default=BillStatus.UNPAID)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.student} - {self.title}"

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def refresh_status(self):
        if self.status == BillStatus.WAIVED:
            return
        if self.amount_paid <= 0:
            self.status = BillStatus.UNPAID
        elif self.amount_paid < self.amount_due:
            self.status = BillStatus.PARTIALLY_PAID
        else:
            self.status = BillStatus.PAID

    def save(self, *args, **kwargs):
        self.refresh_status()
        super().save(*args, **kwargs)


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    BKASH = "BKASH", "bKash"
    NAGAD = "NAGAD", "Nagad"
    BANK = "BANK", "Bank Transfer"
    OTHER = "OTHER", "Other"


class Payment(TimeStampedModel):
    """A payment applied against a Bill. A bill can be paid in installments."""

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    paid_on = models.DateField()
    received_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments_received"
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-paid_on"]

    def __str__(self):
        return f"{self.bill} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # keep the parent bill's paid amount + status in sync
        bill = self.bill
        bill.amount_paid = bill.payments.aggregate(models.Sum("amount"))["amount__sum"] or Decimal("0")
        bill.save(update_fields=["amount_paid", "status", "updated_at"])
