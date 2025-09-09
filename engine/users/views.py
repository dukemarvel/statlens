from rest_framework import viewsets, mixins, permissions
from .models import UserView
from .serializers import UserViewSerializer

class UserViewViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = UserViewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserView.objects.filter(user=self.request.user).order_by("-created_at")
