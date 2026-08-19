import logging
from datetime import date, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import DailyCheck
from .serializers import (
    DailyCheckCreateRequestSerializer,
    DailyCheckCreateResponseSerializer,
    WeeklyChecklistResponseSerializer
)
from care.services import refresh_today_care

logger = logging.getLogger(__name__)

class ChecklistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DailyCheckCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        today = date.today()
        user = request.user

        daily_check, created = DailyCheck.objects.update_or_create(
            user=user,
            check_date=today,
            defaults=validated_data
        )

        # 체크리스트가 등록/수정될 때마다 Rule Engine -> Action 선택 -> LLM 설명 생성을
        # 다시 돌려 '오늘의 케어 추천'을 캐시한다. (GET /care/today/ 는 이 캐시만 읽음)
        # 이 부가 기능이 실패해도 체크리스트 저장 자체는 성공으로 응답해야 하므로 여기서 격리한다.
        try:
            refresh_today_care(user, daily_check)
        except Exception:
            logger.exception("오늘의 케어 추천 갱신 실패 (checklist_id=%s)", daily_check.checklist_id)

        response_data = DailyCheckCreateResponseSerializer(daily_check).data

        return Response(
            {
                "isSuccess": True,
                "code": "SUCCESS",
                "message": "오늘의 데일리 체크리스트가 성공적으로 저장되었습니다.",
                "data": response_data
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )


class WeeklyChecklistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.localdate()

        join_date = user.date_joined.date()

        days_since_joined = (today - join_date).days
        current_day = days_since_joined + 1

        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        records = DailyCheck.objects.filter(
            user=user,
            check_date__range=[start_of_week, end_of_week]
        )
        checked_dates = {record.check_date for record in records}

        weekly_records = []
        is_checklist_done_today = False

        for i in range(7):
            cur_date = start_of_week + timedelta(days=i)
            is_today = (cur_date == today)
            is_checked = cur_date in checked_dates

            if is_today:
                is_checklist_done_today = is_checked

            weekly_records.append({
                "dayOrder": i + 1,
                "date": cur_date.strftime("%Y-%m-%d"),
                "isChecked": is_checked,
                "isToday": is_today
            })

        result = {
            "currentDay": current_day,             
            "isChecklistDone": is_checklist_done_today,
            "weeklyRecords": weekly_records
        }

        serializer = WeeklyChecklistResponseSerializer(result)

        return Response(
            {
                "isSuccess": True,
                "code": "SUCCESS",
                "message": "주간 체크인 현황 조회가 완료되었습니다.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )