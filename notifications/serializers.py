from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notificationId = serializers.IntegerField(source="id", read_only=True)
    type = serializers.CharField(source="notification_type", read_only=True)
    isRead = serializers.BooleanField(source="is_read", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Notification
        fields = ["notificationId", "type", "title", "body", "payload", "isRead", "createdAt"]