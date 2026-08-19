from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(
            {
                "isSuccess": True,
                "code": "SUCCESS",
                "message": "알림 목록 조회가 완료되었습니다.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class NotificationReadView(APIView):
    """PATCH /notifications/{id}/read/ — 알림 하나를 읽음 처리."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        notification = Notification.objects.filter(id=notification_id, user=request.user).first()
        if notification is None:
            return Response(
                {"isSuccess": False, "code": "NOT_FOUND", "message": "알림을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response(
            {
                "isSuccess": True,
                "code": "SUCCESS",
                "message": "읽음 처리되었습니다.",
                "data": NotificationSerializer(notification).data,
            },
            status=status.HTTP_200_OK,
        )