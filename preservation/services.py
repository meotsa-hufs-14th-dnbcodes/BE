from dataclasses import dataclass
from datetime import date

from selfie import client as selfie_client
from .models import PreservationIndex

# 카테고리 PK(proc.Category.id) -> 계산 로직에서 쓰는 카테고리 코드
CATEGORY_ID_TO_CODE = {
    1: "LIFTING",
    2: "SKIN_BOOSTER",
    3: "COLLAGEN_BOOSTER",
    4: "BOTOX",
    5: "FILLER",
    6: "ETC",
}

# 카테고리별로 CV 실측치(metrics) 중 어떤 지표를 볼지
CATEGORY_METRIC_MAP = {
    "FILLER": ["firmness", "wrinkle"],
    "COLLAGEN_BOOSTER": ["firmness", "wrinkle"],
    "BOTOX": ["wrinkle"],
    "LIFTING": ["firmness", "wrinkle"],
    "SKIN_BOOSTER": ["moisture", "firmness"],
    "LASER": ["age_spot", "pore", "redness"],
}

DEFAULT_DURATION_DAYS = 180  # proc_duration이 0/미설정인 경우(예: 기타) 대체값
DAYS_PER_MONTH = 30


def _duration_days(procedure_record) -> int:
    months = procedure_record.procedure.proc_duration
    if not months:
        return DEFAULT_DURATION_DAYS
    return months * DAYS_PER_MONTH


def compute_E(duration_days: int, elapsed_days: int) -> float:
    ratio = min(elapsed_days / duration_days, 1.0)
    return 100 - (100 - FLOOR) * ratio


FLOOR = 20  # 시술 만료 시점 잔존 기대치


@dataclass
class ChecklistInput:
    smoking_yn: bool
    drinking_yn: bool
    uv_protection_yn: bool
    regen_cream_yn: bool 
    intense_exercise_yn: bool 


def _resolve_category_code(procedure_record) -> str:
    category_id = procedure_record.procedure.category_id
    return CATEGORY_ID_TO_CODE.get(category_id, "ETC")


def _metrics_from_analysis(analysis_result: dict) -> dict:
    return {
        d["metric_code"]: d["metric_value"]
        for d in analysis_result.get("details", [])
    }


def compute_A(metrics: dict, category_code: str) -> float:
    keys = CATEGORY_METRIC_MAP.get(category_code, ["all"])
    values = [float(metrics[k]) for k in keys if k in metrics]
    if not values:
        raise ValueError(f"필요한 지표가 응답에 없습니다: {keys}")
    return sum(values) / len(values)


def compute_E(category_code: str, elapsed_days: int) -> float:
    duration = CATEGORY_DURATION_DAYS.get(category_code, 180)
    ratio = min(elapsed_days / duration, 1.0)
    return 100 - (100 - FLOOR) * ratio


def compute_checklist_adjustment(
    checklist: ChecklistInput,
    category_code: str,
    days_since_procedure: int,
) -> int:
    penalty = 0

    if checklist.smoking_yn:
        penalty -= 5
    if checklist.drinking_yn:
        penalty -= 3

    uv_penalty = 8 if category_code == "LASER" else 5
    if not checklist.uv_protection_yn:
        penalty -= uv_penalty

    regen_applicable = category_code in ("LASER", "SKIN_BOOSTER")
    if regen_applicable and not checklist.regen_cream_yn:
        penalty -= 5

    exercise_sensitive = category_code in ("FILLER", "COLLAGEN_BOOSTER", "LIFTING")
    within_risk_window = days_since_procedure <= 7
    if exercise_sensitive and within_risk_window and checklist.intense_exercise_yn:
        penalty -= 3

    return max(penalty, -20)


def calculate_preservation_index(
    user, analysis_id: int, procedure_record, checklist: ChecklistInput
) -> PreservationIndex:
    analysis_result = selfie_client.get_analysis(analysis_id)
    if analysis_result is None:
        raise ValueError(f"analysis_id={analysis_id} 결과를 찾을 수 없습니다.")

    metrics = _metrics_from_analysis(analysis_result)
    category_code = _resolve_category_code(procedure_record)

    today = date.today()
    elapsed_days = (today - procedure_record.procedure_date).days

    a_d = compute_A(metrics, category_code)
    duration_days = _duration_days(procedure_record)
    e_d = compute_E(duration_days, elapsed_days)
    base_index_value = min(a_d / e_d * 100, 100.0)

    adjustment = compute_checklist_adjustment(checklist, category_code, elapsed_days)
    final_index_value = max(0.0, min(100.0, base_index_value + adjustment))

    return PreservationIndex.objects.create(
        user=user,
        analysis_id=analysis_id,
        procedure_record=procedure_record,
        category_code=category_code,
        elapsed_days=elapsed_days,
        a_d=round(a_d, 2),
        e_d=round(e_d, 2),
        base_index_value=round(base_index_value, 2),
        checklist_adjustment=adjustment,
        final_index_value=round(final_index_value, 2),
        checklist_snapshot=checklist.__dict__,
    )
