from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsAdmin, IsAdminOrReadOnly

from .models import Bill, FeeCategory, Payment
from .serializers import BillSerializer, FeeCategorySerializer, PaymentSerializer


class FeeCategoryViewSet(viewsets.ModelViewSet):
    queryset = FeeCategory.objects.all()
    serializer_class = FeeCategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class BillViewSet(viewsets.ModelViewSet):
    """Billing is money — only admin/headteacher can create/edit; class
    teachers can view (read-only) their own students' bills."""

    queryset = Bill.objects.select_related("student", "category").prefetch_related("payments")
    serializer_class = BillSerializer
    filterset_fields = ["student", "status", "category", "academic_year"]
    search_fields = ["student__first_name", "student__last_name", "student__registration_no"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or user.is_admin_or_headteacher:
            return qs
        teacher_profile = getattr(user, "teacher_profile", None)
        if not teacher_profile:
            return qs.none()
        sections = list(teacher_profile.class_teacher_of_sections.values_list("id", flat=True))
        return qs.filter(student__section_id__in=sections)


class PaymentViewSet(viewsets.ModelViewSet):
    """Recording a payment changes money owed — admin/headteacher only."""

    queryset = Payment.objects.select_related("bill", "received_by")
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["bill", "method"]
