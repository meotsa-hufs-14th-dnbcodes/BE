from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkinMetric:
    region: str
    metric_type: str
    score: float
    unit: str | None = None


@dataclass(frozen=True)
class AnalysisResult:
    """poll() 1회 호출의 결과. status는 'running' | 'success' | 'error'."""

    status: str
    metrics: list[SkinMetric] = field(default_factory=list)
    error_code: str | None = None
    raw: dict | None = None


class SkinAnalysisProvider(abc.ABC):
    """
    피부 분석 벤더(PerfectCorp, 룰루랩 등)를 감추는 공통 인터페이스.

    Celery task(tasks.run_skin_analysis)는 이 인터페이스에만 의존한다.
    최종 벤더가 바뀌거나 벤더가 추가되어도 "업로드 → 시작 → 폴링 → 저장" 흐름
    자체는 그대로 유지되고, 벤더별 구현(providers/*.py)만 교체하면 된다.
    """

    name: str

    @abc.abstractmethod
    def upload_image(self, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
        """이미지를 벤더에 업로드하고 file_id(혹은 동등 참조값)를 반환한다."""

    @abc.abstractmethod
    def start_analysis(self, file_id: str) -> str:
        """분석 작업을 시작하고 task_id를 반환한다."""

    @abc.abstractmethod
    def poll(self, task_id: str) -> AnalysisResult:
        """작업 상태를 1회 조회한다. 반복 폴링은 호출자(Celery task)가 담당한다."""

    @property
    @abc.abstractmethod
    def polling_interval_seconds(self) -> float:
        ...
