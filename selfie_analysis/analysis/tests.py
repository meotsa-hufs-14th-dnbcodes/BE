import base64
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import AnalysisStatus, FailReason, SelfieAnalysis
from .providers.base import AnalysisResult, SkinMetric


class _StubProvider:
    name = "stub"
    polling_interval_seconds = 0

    def __init__(self, result: AnalysisResult):
        self._result = result

    def upload_image(self, image_bytes, content_type="image/jpeg"):
        assert image_bytes  
        return "stub-file-id"

    def start_analysis(self, file_id):
        return "stub-task-id"

    def poll(self, task_id):
        return self._result


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class SelfieAnalysisPipelineTests(TestCase):
    def setUp(self):
        self._settings_override = override_settings(INTERNAL_SERVICE_TOKEN="test-token")
        self._settings_override.enable()
        self.addCleanup(self._settings_override.disable)

        self.client = APIClient()
        self.client.credentials(HTTP_X_SERVICE_TOKEN="test-token")

    def _post_selfie(self):
        payload = {
            "user_id": 42,
            "captured_at": "2026-08-14T09:00:00Z",
            "image": base64.b64encode(b"fake-jpeg-bytes").decode(),
        }
        return self.client.post("/api/v1/selfie-analyses/", payload, format="json")
