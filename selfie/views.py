from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

import hmac
from django.conf import settings
from django.contrib.auth import get_user_model
from . import notifications, services


class HasServiceToken(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get("X-Service-Token", "")
        expected = settings.INTERNAL_SERVICE_TOKEN
        return bool(expected) and hmac.compare_digest(token, expected)


class SelfieAnalysisWebhookView(APIView):
    permission_classes = [HasServiceToken]

    def post(self, request):
        data = request.data
        user_id = data.get("user_id")
        analysis_status = data.get("status")
        analysis_id = data.get("analysis_id")

        notifications.notify_analysis_done(
            user_id=user_id,
            status=analysis_status,
            fail_reason=data.get("fail_reason"),
        )

        if analysis_status == "SUCCESS" and analysis_id is not None:
            User = get_user_model()
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(status=status.HTTP_200_OK)
            services.handle_selfie_analysis_success(user, analysis_id)

        return Response(status=status.HTTP_200_OK)


from . import client


class SelfieAnalysisCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        result = client.create_analysis(
            user_id=request.user.id,
            captured_at=data.get("captured_at"),
            image=data.get("image"),
        )
        return Response(result, status=status.HTTP_202_ACCEPTED)



class SelfieAnalysisDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, analysis_id):
        result = client.get_analysis(analysis_id)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result)
