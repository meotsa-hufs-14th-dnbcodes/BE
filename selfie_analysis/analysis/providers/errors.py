"""벤더별 에러 코드를 서비스 공통 FailReason으로 매핑한다.

기능명세서 SELFIE02/03 예외 목록(얼굴 미검출/다중 얼굴/마스크/흔들림/용량 초과/
업로드 실패/API 오류) 기준.
"""

from analysis.models import FailReason

# PerfectCorp Skin Analysis v2.1 문서(요약본)에 등장한 에러 코드 기준.
_PERFECTCORP_ERROR_MAP = {
    "error_no_face": FailReason.NO_FACE,
    "error_src_face_too_small": FailReason.FACE_TOO_SMALL,
    "error_exceed_max_image_size": FailReason.IMAGE_TOO_LARGE,
    "exceed_max_filesize": FailReason.IMAGE_TOO_LARGE,
    "error_nsfw_content_detected": FailReason.UPLOAD_FAILED,
}

_PROVIDER_MAPS = {
    "perfectcorp": _PERFECTCORP_ERROR_MAP,
}


def map_provider_error(provider_name: str, error_code: str | None) -> str:
    provider_map = _PROVIDER_MAPS.get(provider_name, {})
    return provider_map.get(error_code, FailReason.API_ERROR)
