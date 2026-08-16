"""
placeholder 서비스 간(server-to-server) 인증.

기획서 "핵심 기술적 챌린지" 항목에 "서버 간 통신 방식과 인증된 유저 정보를
어떻게 공유할지는 별도로 설계 필요함"이라고 명시된, 아직 미확정인 부분이다.

주의: 이건 "앱 사용자 인증"(로그인 시 무엇을 발급하든 — JWT든 단순 발급 토큰이든,
메인 서버가 알아서 검증할 문제)과는 완전히 다른 계층이다. 이 마이크로서비스는
메인 서버가 사용자를 어떻게 식별했는지 전혀 몰라도 되고, user_id를 평범한 값으로
넘겨받기만 하면 된다. 여기서 다루는 건 오직 "이 호출이 진짜 메인 서버발(發)이
맞는가"뿐이며, 클라이언트(모바일 앱)가 이 토큰을 직접 들고 있어서는 안 된다
(제3자 API 키를 앱에 내장하면 안 되는 것과 같은 이유).

지금은 메인 Django 서버가 고정 시크릿 헤더를 들고 호출한다고 가정한 최소 구현이며,
최종 설계(예: 메인 서버가 호출마다 발급하는 단명 서명값을 이 마이크로서비스가 검증)가
정해지면 이 클래스만 교체하면 되도록 분리해뒀다.
"""

import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasServiceToken(BasePermission):
    message = "유효한 서비스 토큰(X-Service-Token)이 필요합니다."

    def has_permission(self, request, view) -> bool:
        token = request.headers.get("X-Service-Token", "")
        expected = settings.INTERNAL_SERVICE_TOKEN
        return bool(expected) and hmac.compare_digest(token, expected)
