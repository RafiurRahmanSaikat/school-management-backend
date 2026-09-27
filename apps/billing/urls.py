from rest_framework.routers import DefaultRouter

from .views import BillViewSet, FeeCategoryViewSet, PaymentViewSet

router = DefaultRouter(trailing_slash=False)
router.register("fee-categories", FeeCategoryViewSet, basename="feecategory")
router.register("bills", BillViewSet, basename="bill")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls
