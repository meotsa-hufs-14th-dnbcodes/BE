import logging
from datetime import date

from checklist.models import DailyCheck
from preservation import services as preservation_services
from preservation.models import PreservationIndex
from proc.models import ProcedureRecord

from . import actions, openai_client
from .models import TodayCareRecommendation

logger = logging.getLogger(__name__)

FALLBACK_SUMMARY = "오늘의 케어 추천을 준비했어요. 아래 항목을 확인해보세요."


def _build_rule_context(user, daily_check) -> actions.RuleContext:
    checklist = actions.ChecklistSnapshot.from_daily_check(daily_check)

    latest_record = (
        ProcedureRecord.objects.filter(user=user, is_deleted=False)
        .select_related("procedure__category")
        .order_by("-procedure_date", "-created_at")
        .first()
    )

    category_code = None
    elapsed_days = None
    if latest_record is not None and latest_record.procedure is not None:
        category_code = preservation_services.CATEGORY_ID_TO_CODE.get(
            latest_record.procedure.category_id
        )
        elapsed_days = (date.today() - latest_record.procedure_date).days

    latest_index = (
        PreservationIndex.objects.filter(user=user).order_by("-calculated_at").first()
    )
    latest_preservation_index = latest_index.final_index_value if latest_index else None

    return actions.RuleContext(
        checklist=checklist,
        category_code=category_code,
        elapsed_days=elapsed_days,
        latest_preservation_index=latest_preservation_index,
    )


def _catalog_item(action_id: str, text: str) -> dict:
    action = actions.ACTION_CATALOG[action_id]
    return {
        "actionId": action_id,
        "name": action["name"],
        "text": text,
        "effect": action["effect"],
        "duration": action["duration"],
    }


def _generate_items_and_summary(ctx: actions.RuleContext, action_ids: list[str], is_default_routine: bool):

    try:
        llm_context = {
            "categoryCode": ctx.category_code,
            "elapsedDays": ctx.elapsed_days,
            "latestPreservationIndex": ctx.latest_preservation_index,
            "isDefaultRoutine": is_default_routine,
        }
        llm_actions = [
            {
                "actionId": action_id,
                "name": actions.ACTION_CATALOG[action_id]["name"],
                "conditionLabel": actions.ACTION_CATALOG[action_id]["condition_label"],
                "effect": actions.ACTION_CATALOG[action_id]["effect"],
                "duration": actions.ACTION_CATALOG[action_id]["duration"],
            }
            for action_id in action_ids
        ]

        result = openai_client.generate_action_descriptions(llm_context, llm_actions)
        text_by_id = {a["actionId"]: a["text"] for a in result["actions"]}
        if set(text_by_id) != set(action_ids):
            raise openai_client.CareLLMError(
                f"응답 actionId가 요청과 일치하지 않습니다: {sorted(text_by_id)} != {sorted(action_ids)}"
            )

        items = [_catalog_item(action_id, text_by_id[action_id]) for action_id in action_ids]
        summary = str(result["summary"])[:500]
        source = (
            TodayCareRecommendation.SOURCE_DEFAULT_ROUTINE
            if is_default_routine
            else TodayCareRecommendation.SOURCE_LLM
        )
        return items, summary, source

    except openai_client.CareLLMError:
        logger.warning("care LLM 설명 생성 실패, 카탈로그 원문으로 대체합니다.", exc_info=True)
        items = [
            _catalog_item(action_id, actions.ACTION_CATALOG[action_id]["name"])
            for action_id in action_ids
        ]
        source = (
            TodayCareRecommendation.SOURCE_DEFAULT_ROUTINE
            if is_default_routine
            else TodayCareRecommendation.SOURCE_LLM_ERROR
        )
        return items, FALLBACK_SUMMARY, source


def refresh_today_care(user, daily_check) -> TodayCareRecommendation:
    """체크리스트 등록/수정 시점에 호출. Rule Engine을 다시 돌려 캐시를 갱신한다."""

    ctx = _build_rule_context(user, daily_check)
    action_ids, is_default_routine = actions.select_actions(ctx)
    items, summary, source = _generate_items_and_summary(ctx, action_ids, is_default_routine)

    recommendation, _ = TodayCareRecommendation.objects.update_or_create(
        daily_check=daily_check,
        defaults={"summary": summary, "items": items, "source": source},
    )
    return recommendation


def get_today_care(user) -> dict:
    """GET /care/today/ 에서 사용. 캐시된 결과만 읽고 LLM은 호출하지 않는다."""

    daily_check = (
        DailyCheck.objects.filter(user=user, check_date=date.today())
        .select_related("care_recommendation")
        .first()
    )

    if daily_check is None:
        return {"status": "NOT_CHECKED", "summary": "", "items": []}

    recommendation = getattr(daily_check, "care_recommendation", None)
    if recommendation is None:
        return {"status": "NOT_CHECKED", "summary": "", "items": []}

    return {
        "status": "READY",
        "summary": recommendation.summary,
        "items": recommendation.items,
    }
