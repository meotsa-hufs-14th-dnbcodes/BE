"""
파이프라인: Rule Engine(여기) -> Action Catalog 선택(여기) -> LLM 설명 생성(services.py)

주의(데이터 가용성):
  기획서 조건 중 '피부 건조↑', '수분지수↓', '붉은기↑'는 원래 스킨 분석 지표를
  가리키는 것으로 보이지만, 현재 메인 서버(chronoProject)에는 사용자의 "최신
  분석 지표"를 저장/조회하는 경로가 없다(분석 결과는 analysis_id를 알아야만
  조회 가능 - selfie/client.py 참고). 그래서 아래 트리거는 체크리스트/경과일로
  근사한 프록시를 쓴다. 실제 스킨 지표 연동이 준비되면 해당 predicate만 교체하면 됨.

  '수분 섭취 부족'(ACT-009), '수면 부족'(ACT-010)은 아예 추적하는 필드가 없어서
  조건부 트리거가 불가능 -> "추천 가능한 Action 없음" 예외 상황의 기본 루틴으로만 사용.

  '보존지수 급감'(AI 추천 Rule 예시의 마지막 행)은 대응되는 Action ID가 기획서에
  없어서 구현하지 않았다. ACT ID가 정해지면 추가하면 됨.
"""

from dataclasses import dataclass
from typing import Optional

# 시술 카테고리 코드 (preservation.services.CATEGORY_ID_TO_CODE 와 동일) 
ALL_CATEGORIES = "ALL"  

LIFTING_CATEGORIES = ["LIFTING", "SKIN_BOOSTER", "COLLAGEN_BOOSTER"]


@dataclass
class ChecklistSnapshot:
    """오늘 체크리스트가 없으면 전 항목 None(= 알 수 없음)으로 둔다."""

    uv_protection_yn: Optional[bool] = None
    regen_cream_yn: Optional[bool] = None
    smoking_yn: Optional[bool] = None
    drinking_yn: Optional[bool] = None
    intense_exercise_yn: Optional[bool] = None

    @classmethod
    def from_daily_check(cls, daily_check) -> "ChecklistSnapshot":
        if daily_check is None:
            return cls()
        return cls(
            uv_protection_yn=daily_check.uv_protection_yn,
            regen_cream_yn=daily_check.regen_cream_yn,
            smoking_yn=daily_check.smoking_yn,
            drinking_yn=daily_check.drinking_yn,
            intense_exercise_yn=daily_check.intense_exercise_yn,
        )


@dataclass
class RuleContext:
    """Rule Engine이 조건을 평가하는 데 필요한 입력값 묶음."""

    checklist: ChecklistSnapshot
    category_code: Optional[str]          
    elapsed_days: Optional[int]           
    latest_preservation_index: Optional[float]  


def _went_out_without_sunscreen(ctx: RuleContext) -> bool:
    return ctx.checklist.uv_protection_yn is False


def _skin_dry_proxy(ctx: RuleContext) -> bool:
    # 프록시: 오늘 재생크림을 안 발랐으면 건조 위험으로 간주
    return ctx.checklist.regen_cream_yn is False


def _moisture_low_proxy(ctx: RuleContext) -> bool:
    # 프록시: 음주/격한 운동은 수분 손실을 유발
    return bool(ctx.checklist.drinking_yn) or bool(ctx.checklist.intense_exercise_yn)


def _redness_high_proxy(ctx: RuleContext) -> bool:
    # 프록시: 흡연했거나 시술 직후(3일 이내)면 붉은기 위험 상승으로 간주
    return bool(ctx.checklist.smoking_yn) or (
        ctx.elapsed_days is not None and ctx.elapsed_days <= 3
    )


def _within_24h_after_procedure(ctx: RuleContext) -> bool:
    return ctx.elapsed_days is not None and ctx.elapsed_days <= 1


def _within_48h_after_procedure(ctx: RuleContext) -> bool:
    return ctx.elapsed_days is not None and ctx.elapsed_days <= 2


def _within_24_48h_after_procedure(ctx: RuleContext) -> bool:
    return ctx.elapsed_days is not None and 1 <= ctx.elapsed_days <= 2


def _smoking_checked(ctx: RuleContext) -> bool:
    return ctx.checklist.smoking_yn is True


# 케어 행동
# priority: 숫자가 낮을수록 여러 개가 동시에 뜰 때 먼저 노출(응급/안전 > 즉시 케어 > 생활습관)
ACTION_CATALOG = {
    "ACT-001": {
        "name": "재생크림 바르기",
        "categories": LIFTING_CATEGORIES,
        "duration": "1분",
        "condition_label": "피부 건조↑",
        "effect": "피부장벽 회복",
        "predicate": _skin_dry_proxy,
        "priority": 3,
    },
    "ACT-002": {
        "name": "보습크림 바르기",
        "categories": [ALL_CATEGORIES],
        "duration": "1분",
        "condition_label": "수분지수↓",
        "effect": "피부 보습 유지",
        "predicate": _moisture_low_proxy,
        "priority": 5,
    },
    "ACT-003": {
        "name": "자외선 차단제 바르기",
        "categories": [ALL_CATEGORIES],
        "duration": "30초",
        "condition_label": "외출 예정",
        "effect": "색소침착 예방",
        "predicate": _went_out_without_sunscreen,
        "priority": 4,
    },
    "ACT-004": {
        "name": "피부 진정 마스크팩",
        "categories": LIFTING_CATEGORIES,
        "duration": "10분",
        "condition_label": "붉은기↑",
        "effect": "피부 진정",
        "predicate": _redness_high_proxy,
        "priority": 2,
    },
    "ACT-005": {
        "name": "격한 운동 피하기",
        "categories": [ALL_CATEGORIES],
        "duration": "하루",
        "condition_label": "시술 후 24시간",
        "effect": "염증 예방",
        "predicate": _within_24h_after_procedure,
        "priority": 1,
    },
    "ACT-006": {
        "name": "사우나·찜질방 피하기",
        "categories": [ALL_CATEGORIES],
        "duration": "하루",
        "condition_label": "시술 후 48시간",
        "effect": "열 자극 방지",
        "predicate": _within_48h_after_procedure,
        "priority": 1,
    },
    "ACT-007": {
        "name": "음주 피하기",
        "categories": [ALL_CATEGORIES],
        "duration": "하루",
        "condition_label": "시술 후 24~48시간",
        "effect": "회복 촉진",
        "predicate": _within_24_48h_after_procedure,
        "priority": 1,
    },
    "ACT-008": {
        "name": "흡연 자제하기",
        "categories": [ALL_CATEGORIES],
        "duration": "하루",
        "condition_label": "흡연 체크",
        "effect": "회복 지연 예방",
        "predicate": _smoking_checked,
        "priority": 3,
    },
    "ACT-009": {
        "name": "충분한 수분 섭취",
        "categories": [ALL_CATEGORIES],
        "duration": "하루",
        "condition_label": "수분 섭취 부족",
        "effect": "피부 컨디션 유지",
        "predicate": None,  
        "priority": 6,
    },
    "ACT-010": {
        "name": "충분한 수면",
        "categories": [ALL_CATEGORIES],
        "duration": "밤",
        "condition_label": "수면 부족",
        "effect": "피부 회복 지원",
        "predicate": None,  
        "priority": 6,
    },
}


DEFAULT_ROUTINE_ACTION_IDS = ["ACT-002", "ACT-009", "ACT-010"]

MAX_SELECTED_ACTIONS = 3


def _is_category_eligible(action: dict, category_code: Optional[str]) -> bool:
    if ALL_CATEGORIES in action["categories"]:
        return True
    return category_code is not None and category_code in action["categories"]


def select_actions(ctx: RuleContext) -> tuple[list[str], bool]:
    """Rule Engine: 카테고리로 후보군을 좁힌 뒤(Action Catalog 선택), 조건을 만족하는
    Action ID를 우선순위 순으로 최대 MAX_SELECTED_ACTIONS개 반환한다.
    반환값: (action_ids, is_default_routine)
    """

    fired = []
    for action_id, action in ACTION_CATALOG.items():
        predicate = action["predicate"]
        if predicate is None:
            continue
        if not _is_category_eligible(action, ctx.category_code):
            continue
        if predicate(ctx):
            fired.append(action_id)

    if not fired:
        return DEFAULT_ROUTINE_ACTION_IDS[:MAX_SELECTED_ACTIONS], True

    fired.sort(key=lambda action_id: ACTION_CATALOG[action_id]["priority"])
    return fired[:MAX_SELECTED_ACTIONS], False