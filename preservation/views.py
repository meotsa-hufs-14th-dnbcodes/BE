from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from datetime import date
from checklist.models import DailyCheck
from proc.models import ProcedureRecord
from . import services
from .models import PreservationIndex


class PreservationIndexListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        analysis_id = request.query_params.get("analysis_id")
        qs = PreservationIndex.objects.filter(user=request.user)
        if analysis_id is not None:
            qs = qs.filter(analysis_id=analysis_id)

        data = [
            {
                "id": pi.id,
                "analysisId": pi.analysis_id,
                "procedureRecordId": pi.procedure_record_id,
                "categoryCode": pi.category_code,
                "finalIndexValue": pi.final_index_value,
                "calculatedAt": pi.calculated_at,
            }
            for pi in qs
        ]
        return Response(data)

    
    def post(self, request):
        analysis_id = request.data.get("analysis_id")
        if not analysis_id:
            return Response(
                {"detail": "analysis_id는 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        daily_check = DailyCheck.objects.filter(
            user=request.user, check_date=date.today()
        ).first()
        if daily_check is None:
            return Response(
                {"detail": "오늘의 체크리스트가 먼저 등록되어야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        checklist = services.ChecklistInput(
            smoking_yn=daily_check.smoking_yn,
            drinking_yn=daily_check.drinking_yn,
            uv_protection_yn=daily_check.uv_protection_yn,
            regen_cream_yn=daily_check.regen_cream_yn,
            intense_exercise_yn=daily_check.intense_exercise_yn,
        )

        records = ProcedureRecord.objects.filter(
            user=request.user, is_deleted=False
        ).select_related("procedure")

        results = []
        for record in records:
            try:
                pi = services.calculate_preservation_index(
                    user=request.user,
                    analysis_id=analysis_id,
                    procedure_record=record,
                    checklist=checklist,
                )
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            results.append(pi)

        data = [
            {
                "id": pi.id,
                "procedureRecordId": pi.procedure_record_id,
                "categoryCode": pi.category_code,
                "finalIndexValue": pi.final_index_value,
            }
            for pi in results
        ]
        return Response(data, status=status.HTTP_201_CREATED)