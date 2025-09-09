from rest_framework import serializers
from .models import UserView

class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserView
        fields = ["id", "name", "metric_keys", "filters", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
