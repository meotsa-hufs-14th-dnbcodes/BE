from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnalysisStatus, SelfieAnalysis
from .permissions import HasServiceToken
from .serializers import SelfieAnalysisSerializer, SelfieUploadSerializer
from .tasks import run_skin_analysis


class SelfieAnalysisCreateView(APIView):
    """
    SELFIE02(셀카 촬영 및 업로드): 암호화된 셀카를 받아 분석을 큐에 올린다.
    분석 자체는 몇 초~몇십 초 걸릴 수 있으므로 절대 동기로 기다리지 않고,
    즉시 202 + analysis_id만 돌려준다. 실제 결과는 상태 조회 엔드포인트를 폴링해서 받는다.
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

        run_skin_analysis.delay(
            analysis.analysis_id,
            payload["encrypted_key"],
            payload["nonce"],
            payload["ciphertext"],
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
