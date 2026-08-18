from datetime import date, timedelta
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

class ChecklistAPIView(APIView):

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
    def get(self, request, *args, **kwargs):
        user = request.user
        today = date.today()

        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        records = DailyCheck.objects.filter(
            user=user,
            check_date__range=[start_of_week, end_of_week]
        )
        checked_dates = {record.check_date for record in records}

        weekly_records = []
        is_checklist_done_today = False
        current_day_order = today.weekday() + 1
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
            "currentDay": current_day_order,
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