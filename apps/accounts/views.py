from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsAdminOrReadOnly

from .models import User
from .serializers import UserCreateSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Full control for admin/headteacher (create/update/deactivate any account).
    Everyone authenticated can read the directory (needed to pick a "class
    teacher" dropdown, etc).
    """

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ["role", "gender", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email", "phone"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer
