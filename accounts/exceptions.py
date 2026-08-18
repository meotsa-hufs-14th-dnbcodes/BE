from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    """
    DRF 기본 인증 실패 응답({"detail": "..."})을
    API 명세 형식({"error": "unauthorized"})으로 통일.
    """
    response = drf_exception_handler(exc, context)

    if response is not None and response.status_code == 401:
        response.data = {"error": "unauthorized"}

    return response