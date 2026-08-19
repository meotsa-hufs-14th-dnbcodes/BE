from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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

        required_fields = [
            "smoking_yn", "drinking_yn", "uv_protection_yn",
            "regen_cream_yn", "intense_exercise_yn",
        ]

        checklist_data = request.data.get("checklist")
        if not isinstance(checklist_data, dict) or any(
            field not in checklist_data for field in required_fields
        ):
            return Response(
                {"detail": f"checklist는 필수이며 다음 필드를 모두 포함해야 합니다: {required_fields}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        checklist = services.ChecklistInput(**{f: checklist_data[f] for f in required_fields})

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