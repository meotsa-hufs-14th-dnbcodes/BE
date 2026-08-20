import logging
from datetime import date, timedelta

from django.db.models import Avg

from preservation.models import PreservationIndex
from proc.models import ProcedureRecord

from .models import Notification

logger = logging.getLogger(__name__)

# 재시술 알림을 며칠 전에 띄울지 (고정값)
RETREATMENT_LEAD_DAYS = [30, 14, 7, 1]


def _get_or_create(user_id, notification_type, dedupe_key, title, body, payload=None):
    return Notification.objects.get_or_create(
        user_id=user_id,
        dedupe_key=dedupe_key,
        defaults={
            "notification_type": notification_type,
            "title": title,
            "body": body,
            "payload": payload or {},
        },
    )


# 재시술 알림
def generate_retreatment_notifications(today: date = None) -> int:
    today = today or date.today()
    created_count = 0

    records = (
        ProcedureRecord.objects.filter(is_deleted=False)
        .select_related("procedure")
    )

    for record in records:
        duration_days = record.procedure.reminder_duration_days
        if not duration_days:
            continue

        expected_date = record.procedure_date + timedelta(days=duration_days)

        for lead_days in RETREATMENT_LEAD_DAYS:
            trigger_date = expected_date - timedelta(days=lead_days)
            if trigger_date != today:
                continue

            dedupe_key = f"retreatment:{record.record}:{lead_days}"
            _, created = _get_or_create(
                user_id=record.user_id,
                notification_type=Notification.TYPE_RETREATMENT,
                dedupe_key=dedupe_key,
                title=f"'{record.proc_name}'의 재시술 시점이 다가와요!",
                body=f"예상 효과 소실일 {expected_date.strftime('%m월 %d일')} · D-{lead_days}",
                payload={
                    "procedureRecordId": record.record,
                    "procCode": record.procedure_id,
                    "procName": record.proc_name,
                    "expectedDate": expected_date.isoformat(),
                    "leadDays": lead_days,
                },
            )
            if created:
                created_count += 1

    logger.info("재시술 알림 생성: %d건 (기준일=%s)", created_count, today)
    return created_count


# 오늘의 케어 알림
def notify_today_care(daily_check, recommendation) -> Notification:
    items = recommendation.items or []
    if items:
        first_name = items[0].get("name", "케어")
        body = f"{first_name} 등 {len(items)}가지 루틴이 남았습니다."
    else:
        body = recommendation.summary or "오늘의 케어 추천을 확인해보세요."

    dedupe_key = f"today_care:{daily_check.check_date.isoformat()}"
    notification, _ = Notification.objects.update_or_create(
        user_id=daily_check.user_id,
        dedupe_key=dedupe_key,
        defaults={
            "notification_type": Notification.TYPE_TODAY_CARE,
            "title": "오늘의 케어 루틴",
            "body": body,
            "payload": {
                "checklistId": daily_check.checklist_id,
                "summary": recommendation.summary,
                "items": items,
            },
        },
    )
    return notification

# 보존지수 리포트 알림 
def _week_bounds(reference: date):
    monday = reference - timedelta(days=reference.weekday())
    next_monday = monday + timedelta(days=7)
    return monday, next_monday


def generate_weekly_report_notifications(today: date = None) -> int:

    today = today or date.today()
    this_monday, next_monday = _week_bounds(today)
    last_monday = this_monday - timedelta(days=7)

    user_ids = (
        PreservationIndex.objects.filter(
            calculated_at__date__gte=this_monday, calculated_at__date__lt=next_monday
        )
        .values_list("user_id", flat=True)
        .distinct()
    )

    created_count = 0
    for user_id in user_ids:
        this_avg = PreservationIndex.objects.filter(
            user_id=user_id, calculated_at__date__gte=this_monday, calculated_at__date__lt=next_monday
        ).aggregate(avg=Avg("final_index_value"))["avg"]

        if this_avg is None:
            continue

        last_avg = PreservationIndex.objects.filter(
            user_id=user_id, calculated_at__date__gte=last_monday, calculated_at__date__lt=this_monday
        ).aggregate(avg=Avg("final_index_value"))["avg"]

        point_diff = round(this_avg - last_avg, 1) if last_avg is not None else None
        percent_change = (
            round((this_avg - last_avg) / last_avg * 100, 1) if last_avg else None
        )

        if point_diff is None:
            trend_text = "지난 주 데이터가 없어 비교할 수 없어요."
        else:
            arrow = "상승" if point_diff >= 0 else "하락"
            sign = "+" if point_diff >= 0 else ""
            trend_text = f"전주 대비 {sign}{point_diff}p {arrow}"

        dedupe_key = f"weekly_report:{this_monday.isoformat()}"
        _, created = _get_or_create(
            user_id=user_id,
            notification_type=Notification.TYPE_WEEKLY_REPORT,
            dedupe_key=dedupe_key,
            title="주간 보존지수 리포트",
            body=f"이번 주 평균 {round(this_avg, 1)} — {trend_text}",
            payload={
                "weekStart": this_monday.isoformat(),
                "weekAverage": round(this_avg, 1),
                "prevWeekAverage": round(last_avg, 1) if last_avg is not None else None,
                "pointDiff": point_diff,
                "percentChange": percent_change,
            },
        )
        if created:
            created_count += 1

    logger.info("주간 리포트 알림 생성: %d건 (주 시작=%s)", created_count, this_monday)
    return created_count
