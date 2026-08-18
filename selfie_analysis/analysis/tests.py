import base64
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import AnalysisStatus, FailReason, SelfieAnalysis
from .providers.base import AnalysisResult, SkinMetric


def _encrypt_for_test(image_bytes: bytes, public_key) -> dict:
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = b"0" * 12
    ciphertext = AESGCM(aes_key).encrypt(nonce, image_bytes, None)
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return {
        "encrypted_key": base64.b64encode(encrypted_key).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }


class _StubProvider:
    # 벤더 호출을 흉내내는 테스트 전용 provider (실제 네트워크를 타지 않음)

    name = "stub"
    polling_interval_seconds = 0

    def __init__(self, result: AnalysisResult):
        self._result = result

    def upload_image(self, image_bytes, content_type="image/jpeg"):
        assert image_bytes  # 복호화가 실제로 원본 바이트를 복원했는지 확인
        return "stub-file-id"

    def start_analysis(self, file_id):
        return "stub-task-id"

    def poll(self, task_id):
        return self._result


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class SelfieAnalysisPipelineTests(TestCase):
    def setUp(self):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        self._settings_override = override_settings(
            SELFIE_UPLOAD_RSA_PRIVATE_KEY=pem, INTERNAL_SERVICE_TOKEN="test-token"
        )
        self._settings_override.enable()
        self.addCleanup(self._settings_override.disable)

        self.client = APIClient()
        self.client.credentials(HTTP_X_SERVICE_TOKEN="test-token")

    def _post_selfie(self):
        payload = _encrypt_for_test(b"fake-jpeg-bytes", self.private_key.public_key())
        payload["user_id"] = 42
        payload["captured_at"] = "2026-08-14T09:00:00Z"
        return self.client.post("/api/v1/selfie-analyses/", payload, format="json")

    def test_rejects_missing_service_token(self):
        self.client.credentials()
        response = self._post_selfie()
        self.assertEqual(response.status_code, 403)

    @patch("analysis.tasks.get_provider")
    def test_success_pipeline_stores_details(self, mock_get_provider):
        mock_get_provider.return_value = _StubProvider(
            AnalysisResult(
                status="success",
                metrics=[SkinMetric(metric_type="moisture", score=72.5)],
            )
        )

        create_response = self._post_selfie()
        self.assertEqual(create_response.status_code, 202)
        analysis_id = create_response.data["analysis_id"]

        analysis = SelfieAnalysis.objects.get(pk=analysis_id)
        self.assertEqual(analysis.status, AnalysisStatus.SUCCESS)
        self.assertEqual(analysis.details.count(), 1)

        detail_response = self.client.get(f"/api/v1/selfie-analyses/{analysis_id}/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["status"], "SUCCESS")
        self.assertEqual(detail_response.data["details"][0]["metric_code"], "moisture")

    @patch("analysis.tasks.get_provider")
    def test_vendor_error_maps_to_fail_reason(self, mock_get_provider):
        stub = _StubProvider(AnalysisResult(status="error", error_code="error_no_face"))
        stub.name = "perfectcorp"  # 실제 벤더 이름으로 error map을 태워본다
        mock_get_provider.return_value = stub

        create_response = self._post_selfie()
        analysis_id = create_response.data["analysis_id"]

        analysis = SelfieAnalysis.objects.get(pk=analysis_id)
        self.assertEqual(analysis.status, AnalysisStatus.FAIL)
        self.assertEqual(analysis.fail_reason, FailReason.NO_FACE)
