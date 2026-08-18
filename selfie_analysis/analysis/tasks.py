from __future__ import annotations

import logging
import time

from celery import shared_task
from django.conf import settings

from .crypto import DecryptionError, decrypt_selfie_payload
from .models import AnalysisStatus, FailReason, SelfieAnalysis, SelfieAnalysisDetail
from .providers import get_provider
from .providers.errors import map_provider_error

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def run_skin_analysis(self, analysis_id: int, encrypted_key: str, nonce: str, ciphertext: str):
    """
    업로드 즉시 202로 응답한 뒤 백그라운드에서 도는 전체 파이프라인:
    복호화 → 벤더 업로드 → 분석 시작 → 폴링 → 결과 저장/상태 갱신.
    원본 이미지 바이트는 이 함수 실행 중에만 메모리에 존재한다.
    """
    try:
        analysis = SelfieAnalysis.objects.get(pk=analysis_id)
    except SelfieAnalysis.DoesNotExist:
        logger.warning("SelfieAnalysis %s not found, dropping task", analysis_id)
        return

    try:
        image_bytes = decrypt_selfie_payload(encrypted_key, nonce, ciphertext)
    except DecryptionError as exc:
        logger.warning("decrypt failed for analysis %s: %s", analysis_id, exc)
        _mark_fail(analysis, FailReason.UPLOAD_FAILED)
        return

    provider = get_provider()
    analysis.provider = provider.name
    analysis.save(update_fields=["provider", "updated_at"])

    try:
        file_id = provider.upload_image(image_bytes)
    except Exception:
        logger.exception("upload_image failed for analysis %s", analysis_id)
        _mark_fail(analysis, FailReason.UPLOAD_FAILED)
        return
    finally:
        # 벤더 업로드가 끝났으니(성공하든 실패하든) 원본 바이트 참조를 더 들고 있지 않는다.
        del image_bytes

    analysis.provider_file_id = file_id
    analysis.save(update_fields=["provider_file_id", "updated_at"])

    try:
        task_id = provider.start_analysis(file_id)
    except Exception:
        logger.exception("start_analysis failed for analysis %s", analysis_id)
        _mark_fail(analysis, FailReason.API_ERROR)
        return

    analysis.provider_task_id = task_id
    analysis.save(update_fields=["provider_task_id", "updated_at"])

    result = _poll_until_done(provider, task_id, analysis_id)
    if result is None:
        # 타임아웃: "API 오류 시 이전 데이터 유지" 원칙 — 직전 결과는 건드리지 않고 FAIL만 기록
        _mark_fail(analysis, FailReason.API_ERROR)
        return

    if result.status == "error":
        _mark_fail(analysis, map_provider_error(provider.name, result.error_code))
        return

    SelfieAnalysisDetail.objects.bulk_create(
        [
            SelfieAnalysisDetail(
                analysis=analysis,
                metric_code=metric.metric_type,
                metric_value=metric.score,
                metric_unit=metric.unit,
            )
            for metric in result.metrics
        ]
    )
    analysis.status = AnalysisStatus.SUCCESS
    analysis.fail_reason = None
    analysis.save(update_fields=["status", "fail_reason", "updated_at"])


def _poll_until_done(provider, task_id: str, analysis_id: int):
    max_wait = settings.SKIN_ANALYSIS_POLL_TIMEOUT_SECONDS
    interval = provider.polling_interval_seconds
    elapsed = 0.0

    while elapsed <= max_wait:
        result = provider.poll(task_id)
        if result.status in ("success", "error"):
            return result
        time.sleep(interval)
        elapsed += interval

    logger.warning("polling timed out for analysis %s (task %s)", analysis_id, task_id)
    return None


def _mark_fail(analysis: SelfieAnalysis, fail_reason: str) -> None:
    analysis.status = AnalysisStatus.FAIL
    analysis.fail_reason = fail_reason
    analysis.save(update_fields=["status", "fail_reason", "updated_at"])
