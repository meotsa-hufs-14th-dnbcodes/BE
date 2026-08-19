import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = (
    "너는 피부 시술 후 관리를 돕는 케어 코치야. 아래 지시를 반드시 지켜.\n"
    "입력으로 오늘 추천하기로 '이미 확정된' 케어 행동 목록을 줄게. 새로운 행동을 "
    "만들거나 목록에 없는 행동을 추가하지 마. 각 행동이 왜 필요한지, 지켰을 때 "
    "어떤 효과가 있는지만 한국어로 자연스럽게 설명해.\n\n"
    "반드시 아래 JSON 형식으로만 답해. 다른 설명은 절대 붙이지 마.\n"
    "{\n"
    '  "summary": "오늘 상태와 추천 행동을 아우르는 한국어 요약. 공백 포함 200자 내외.",\n'
    '  "actions": [\n'
    '    {"actionId": "ACT-XXX", "text": "이 행동을 왜/어떻게 해야 하는지 2문장 (100자 내외)"}\n'
    "  ]\n"
    "}\n\n"
    "actions 배열의 actionId와 개수는 입력받은 목록과 정확히 동일해야 해."
)


class CareLLMError(Exception):
    pass


def generate_action_descriptions(context: dict, actions: list[dict]) -> dict:
    """
    context: 오늘 체크리스트/경과일 등 요약 정보(dict, 자유 형식)
    actions: [{"actionId": "ACT-004", "name": "피부 진정 마스크팩",
               "conditionLabel": "붉은기↑", "effect": "피부 진정", "duration": "10분"}, ...]
    반환값: {"summary": str, "actions": [{"actionId": str, "text": str}, ...]}
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise CareLLMError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    user_prompt = json.dumps(
        {"context": context, "actions": actions}, ensure_ascii=False
    )

    try:
        resp = requests.post(
            OPENAI_CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.6,
                "response_format": {"type": "json_object"},
            },
            timeout=8,
        )
    except requests.RequestException as exc:
        raise CareLLMError(f"OpenAI 호출 실패: {exc}") from exc

    if resp.status_code != 200:
        raise CareLLMError(f"OpenAI 응답 오류 status={resp.status_code} body={resp.text}")

    try:
        content = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, ValueError) as exc:
        raise CareLLMError(f"OpenAI 응답 파싱 실패: {exc}") from exc

    if "summary" not in parsed or "actions" not in parsed:
        raise CareLLMError(f"OpenAI 응답 형식이 올바르지 않습니다: {parsed}")

    return parsed