"""
PerfectCorp (YouCam) AI Skin Analysis API v2.1 클라이언트.

확인된 사항 (docs.perfectcorp.com 문서 기준):
  - POST /s2s/v2.0/task/skin-analysis            : 분석 작업 시작, task_id 반환
  - GET  /s2s/v2.0/task/skin-analysis/{task_id}  : 상태 폴링, task_status(running/success/error)
  - 인증: Authorization: Bearer <API_KEY> 헤더
  - v2.1은 유료 결제 플랜 전용이라 v2.0으로 고정.

미확인 사항 (파일 업로드):
  - "File API"에 요청하면 file_id와 업로드용 requests[].url을 응답으로 받고,
    그 url로 이미지를 업로드한다는 흐름은 문서에 있으나, File API의 정확한
    엔드포인트 경로/HTTP 메서드는 공개 문서 발췌본에 없었다.
  - 그래서 경로를 하드코딩하지 않고 settings.PERFECTCORP_FILE_UPLOAD_PATH로 뺐음.
    API 콘솔(https://yce.makeupar.com/api-console/en/api-keys/) 또는 전체 레퍼런스에서
    확정한 뒤 .env에 채워 넣을 것. 미설정 시 명확한 예외를 던진다.
"""

from __future__ import annotations

import requests
from django.conf import settings

from .base import AnalysisResult, SkinAnalysisProvider, SkinMetric
from .errors import map_provider_error


class PerfectCorpConfigError(RuntimeError):
    pass


def _to_metric(item: dict) -> SkinMetric:
    # 대부분 지표는 ui_score(0-100 정규화)로 오고, "all"/"skin_age"만 score로 온다.
    score = item["ui_score"] if "ui_score" in item else item["score"]
    return SkinMetric(metric_type=item["type"], score=float(score))


class PerfectCorpProvider(SkinAnalysisProvider):
    name = "perfectcorp"

    def __init__(self):
        self.base_url = settings.PERFECTCORP_BASE_URL.rstrip("/")
        self.api_key = settings.PERFECTCORP_API_KEY
        self.dst_actions = settings.PERFECTCORP_DST_ACTIONS
        self.file_upload_path = settings.PERFECTCORP_FILE_UPLOAD_PATH

        if not self.api_key:
            raise PerfectCorpConfigError("PERFECTCORP_API_KEY가 설정되지 않았습니다.")
        if not self.base_url:
            raise PerfectCorpConfigError(
                "PERFECTCORP_BASE_URL이 설정되지 않았습니다. API 콘솔에서 S2S 호출용 "
                "base host를 확인해 .env에 설정하세요."
            )

        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    @property
    def polling_interval_seconds(self) -> float:
        return settings.PERFECTCORP_POLL_INTERVAL_SECONDS

    def upload_image(self, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
        if not self.file_upload_path:
            raise PerfectCorpConfigError(
                "PERFECTCORP_FILE_UPLOAD_PATH가 설정되지 않았습니다. "
                "PerfectCorp File API의 정확한 엔드포인트를 확인해 .env에 설정하세요."
            )

        extension = content_type.split("/")[-1]
        resp = self._session.post(
            f"{self.base_url}{self.file_upload_path}",
            json={
                "files": [
                    {
                        "content_type": content_type,
                        "file_name": f"selfie.{extension}",
                        "file_size": len(image_bytes),
                    }
                ]
            },
            timeout=30,
        )
        resp.raise_for_status()
        file_info = resp.json()["data"]["files"][0]

        file_id = file_info["file_id"]
        upload_request = file_info["requests"][0]
        upload_url = upload_request["url"]
        upload_headers = upload_request.get("headers", {})

        put_resp = requests.put(
            upload_url, data=image_bytes, headers=upload_headers, timeout=60
        )
        put_resp.raise_for_status()
        return file_id

    def start_analysis(self, file_id: str) -> str:
        resp = self._session.post(
            f"{self.base_url}/s2s/v2.0/task/skin-analysis",
            json={
                "src_file_id": file_id,
                "dst_actions": self.dst_actions,
                "format": "json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["data"]["task_id"]

    def poll(self, task_id: str) -> AnalysisResult:
        resp = self._session.get(
            f"{self.base_url}/s2s/v2.0/task/skin-analysis/{task_id}", timeout=30
        )
        resp.raise_for_status()
        payload = resp.json()
        data = payload["data"]
        status = data["task_status"]

        if status == "success":
            output = data.get("results", {}).get("output", [])
            metrics = [_to_metric(item) for item in output if item["type"] != "resize_image"]
            return AnalysisResult(status="success", metrics=metrics, raw=payload)

        if status == "error":
            error = data.get("error")
            error_code = error.get("code") if isinstance(error, dict) else error
            return AnalysisResult(
                status="error", error_code=str(error_code) if error_code else None, raw=payload
            )

        return AnalysisResult(status="running", raw=payload)

    def map_error(self, error_code: str | None) -> str:
        return map_provider_error(self.name, error_code)
