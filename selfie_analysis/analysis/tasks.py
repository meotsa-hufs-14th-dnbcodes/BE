from __future__ import annotations

import logging

from .crypto import DecryptionError, decrypt_selfie_payload
from .models import AnalysisStatus, FailReason, SelfieAnalysis, SelfieAnalysisDetail
from .providers import get_provider
from .providers.errors import map_provider_error

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def start_skin_analysis(analysis_id: int, encrypted_key: str, nonce: str, ciphertext: str):
    """
    업로드 요청 안에서 동기로 실행: 복호화 → 벤더 업로드 → 분석 시작.
    실제 분석 완료/결과 저장은 PerfectCorp webhook이 오면 complete_skin_analysis가 처리
    """
    try:
        analysis = SelfieAnalysis.objects.get(pk=analysis_id)
    except SelfieAnalysis.DoesNotExist:
        logger.warning("SelfieAnalysis %s not found, dropping request", analysis_id)
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


def complete_skin_analysis(task_id: str):
    """
    PerfectCorp webhook이 완료(success/error)를 알려오면 호출된다.
    webhook 바디엔 task_status만 있고 실제 결과는 없으므로, poll()을 한 번 더 불러 받아온다.
    """
    try:
        analysis = SelfieAnalysis.objects.get(provider_task_id=task_id)
    except SelfieAnalysis.DoesNotExist:
        logger.warning("no SelfieAnalysis for provider_task_id=%s, dropping webhook", task_id)
        return

    if analysis.status != AnalysisStatus.PENDING:
        # webhook 재전송 등으로 이미 처리된 건 — 멱등하게 무시
        logger.info(
            "analysis %s already resolved (status=%s), ignoring webhook",
            analysis.analysis_id, analysis.status,
        )
        return

    provider = get_provider()

    try:
        result = provider.poll(task_id)
    except Exception:
        logger.exception("poll failed for task %s", task_id)
        _mark_fail(analysis, FailReason.API_ERROR)
        return

    if result.status == "error":
        _mark_fail(analysis, map_provider_error(provider.name, result.error_code))
        return

    if result.status != "success":
        # webhook은 왔는데 아직 running이면 예상 밖 상황. API 오류로 처리
        logger.warning("webhook fired but task %s still %s", task_id, result.status)
        _mark_fail(analysis, FailReason.API_ERROR)
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
    _notify_chrono(analysis)


def _mark_fail(analysis: SelfieAnalysis, fail_reason: str) -> None:
    analysis.status = AnalysisStatus.FAIL
    analysis.fail_reason = fail_reason
    analysis.save(update_fields=["status", "fail_reason", "updated_at"])
    _notify_chrono(analysis)


def _notify_chrono(analysis):
    try:
        requests.post(
            settings.CHRONO_WEBHOOK_URL,
            json={
                "user_id": analysis.user_id,
                "status": analysis.status,
                "fail_reason": analysis.fail_reason,
            },
            headers={"X-Service-Token": settings.INTERNAL_SERVICE_TOKEN},
            timeout=5,
        )
    except requests.RequestException:
        logger.exception("failed to notify chronoProject for analysis %s", analysis.analysis_id)