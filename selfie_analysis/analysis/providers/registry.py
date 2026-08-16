from django.conf import settings

from .base import SkinAnalysisProvider


def get_provider() -> SkinAnalysisProvider:
    """
    settings.SKIN_ANALYSIS_PROVIDER 값에 따라 벤더 구현체를 반환한다.
    기획서상 1차 벤더는 "룰루랩 등 상용 API"로 언급되어 있고 PerfectCorp은
    별도 검토 중이므로, 최종 벤더가 바뀌면 여기 매핑에 한 줄만 추가하면 된다.
    """
    provider_name = settings.SKIN_ANALYSIS_PROVIDER

    if provider_name == "perfectcorp":
        from .perfectcorp import PerfectCorpProvider

        return PerfectCorpProvider()

    raise ValueError(f"알 수 없는 SKIN_ANALYSIS_PROVIDER: {provider_name!r}")
