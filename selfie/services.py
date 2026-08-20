import logging
from datetime import date

from checklist.models import DailyCheck
from preservation import services as preservation_services
from proc.models import ProcedureRecord

from .models import PendingPreservationCalc

logger = logging.getLogger(__name__)


def _run_calculation(user, analysis_id, daily_check):
    checklist = preservation_services.ChecklistInput(
        smoking_yn=daily_check.smoking_yn,
        drinking_yn=daily_check.drinking_yn,
        uv_protection_yn=daily_check.uv_protection_yn,
        regen_cream_yn=daily_check.regen_cream_yn,
        intense_exercise_yn=daily_check.intense_exercise_yn,
    )

    records = ProcedureRecord.objects.filter(
        user=user, is_deleted=False
    ).select_related("procedure")

    created = 0
    for record in records:
        try:
            preservation_services.calculate_preservation_index(
                user=user,
                analysis_id=analysis_id,
                procedure_record=record,
                checklist=checklist,
            )
            created += 1
        except ValueError:
            logger.exception(
                "보존지수 자동 계산 실패: user=%s analysis_id=%s record=%s",
                user.id, analysis_id, record.pk,
            )

    logger.warning(
        "보존지수 자동 계산 완료: user=%s analysis_id=%s 생성=%s건",
        user.id, analysis_id, created,
    )


def handle_selfie_analysis_success(user, analysis_id):
    """셀카 분석 SUCCESS 웹훅 수신 시 호출.
    오늘 체크리스트가 이미 있으면 바로 계산하고, 없으면 대기열에 저장해뒀다가
    checklist 쪽에서 체크리스트가 등록될 때 마저 처리하게 한다."""
    logger.warning("handle_selfie_analysis_success 호출됨: user=%s analysis_id=%s", user.id, analysis_id)

    daily_check = DailyCheck.objects.filter(user=user, check_date=date.today()).first()
    if daily_check is None:
        logger.warning(
            "user=%s 오늘(%s) 체크리스트 없음 → 대기열에 저장", user.id, date.today()
        )
        PendingPreservationCalc.objects.update_or_create(
            user=user,
            check_date=date.today(),
            defaults={"analysis_id": analysis_id},
        )
        return

    _run_calculation(user, analysis_id, daily_check)


def handle_daily_check_saved(user, daily_check):
    """체크리스트 생성/수정 시 호출.
    그날짜로 대기 중인(셀카 분석은 먼저 끝났지만 체크리스트가 없어 미뤄둔) 계산이 있으면 마저 처리한다."""
    pending = PendingPreservationCalc.objects.filter(
        user=user, check_date=daily_check.check_date
    ).first()
    if pending is None:
        return

    logger.warning(
        "대기 중이던 보존지수 계산 처리: user=%s analysis_id=%s", user.id, pending.analysis_id
    )
    _run_calculation(user, pending.analysis_id, daily_check)
    pending.delete()
