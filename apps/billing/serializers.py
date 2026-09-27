from rest_framework import serializers

from .models import Bill, FeeCategory, Payment


class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = ["id", "name", "description"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "bill", "amount", "method", "paid_on", "received_by", "note"]


class BillSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id", "student", "student_name", "category", "academic_year", "title",
            "amount_due", "amount_paid", "balance", "due_date", "status", "payments",
        ]
        read_only_fields = ["amount_paid", "status"]
