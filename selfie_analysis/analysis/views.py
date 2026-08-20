import logging

from django.conf import settings
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from standardwebhooks.webhooks import Webhook, WebhookVerificationError

from .models import AnalysisStatus, SelfieAnalysis
from .permissions import HasServiceToken
from .serializers import SelfieAnalysisSerializer, SelfieUploadSerializer
from .tasks import complete_skin_analysis, start_skin_analysis

logger = logging.getLogger(__name__)


class SelfieAnalysisCreateView(APIView):
    """
    SELFIE02(셀카 촬영 및 업로드): 암호화된 셀카를 받아 분석을 시작한다.
    복호화~벤더 분석 시작까지는 이 요청 안에서 동기로 처리하고(수 초),
    실제 분석 완료는 PerfectCorp webhook을 통해 비동기로 알려온다.
    즉시 202 + analysis_id를 돌려주고, 최종 결과는 상태 조회 엔드포인트로 확인한다.
    """

    permission_classes = [HasServiceToken]

    def post(self, request):
        serializer = SelfieUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        analysis = SelfieAnalysis.objects.create(
            user_id=payload["user_id"],
            captured_at=payload["captured_at"],
            status=AnalysisStatus.PENDING,
        )

        start_skin_analysis(
            analysis.analysis_id,
            payload["image"],
        )

        return Response(
            {"analysis_id": analysis.analysis_id, "status": analysis.status},
            status=status.HTTP_202_ACCEPTED,
        )


class SelfieAnalysisDetailView(RetrieveAPIView):
    """상태 조회 폴링 엔드포인트. SUCCESS면 부위별 수치(details)까지 함께 내려준다."""

    permission_classes = [HasServiceToken]
    queryset = SelfieAnalysis.objects.prefetch_related("details")
    serializer_class = SelfieAnalysisSerializer
    lookup_url_kwarg = "analysis_id"
    lookup_field = "analysis_id"


class PerfectCorpWebhookView(APIView):
    """
    PerfectCorp이 분석 완료(success/error) 시 호출하는 webhook 수신 엔드포인트.
    호출 주체가 메인 서버가 아니라 PerfectCorp이므로 HasServiceToken이 아니라
    Standard Webhooks 서명(HMAC-SHA256)으로 검증한다.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        headers = {
            "webhook-id": request.headers.get("webhook-id", ""),
            "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
            "webhook-signature": request.headers.get("webhook-signature", ""),
        }

        wh = Webhook(settings.PERFECTCORP_WEBHOOK_SECRET)
        try:
            payload = wh.verify(request.body, headers)
        except WebhookVerificationError:
            logger.warning("PerfectCorp webhook signature verification failed")
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        task_id = payload["data"]["taskId"]
        complete_skin_analysis(task_id)

        return Response(status=status.HTTP_200_OK)

class PerfectCorpWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        headers = {
            "webhook-id": request.headers.get("webhook-id", ""),
            "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
            "webhook-signature": request.headers.get("webhook-signature", ""),
        }

        wh = Webhook(settings.PERFECTCORP_WEBHOOK_SECRET)
        try:
            payload = wh.verify(request.body, headers)
        except WebhookVerificationError:
            logger.warning("PerfectCorp webhook signature verification failed")
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        logger.info("PerfectCorp webhook payload: %s", payload)  # 추가 — 실제 바디 확인용

        try:
            task_id = payload["data"]["task_id"]
        except KeyError:
            logger.error("PerfectCorp webhook에 task_id가 없습니다: %s", payload)
            return Response(status=status.HTTP_200_OK)  # PerfectCorp 재시도 폭주 방지

        complete_skin_analysis(task_id)
        return Response(status=status.HTTP_200_OK)
