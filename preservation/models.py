from django.db import models
from django.conf import settings

from proc.models import ProcedureRecord


class PreservationIndex(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preservation_indices",
        verbose_name="사용자",
    )
    analysis_id = models.PositiveIntegerField(verbose_name="분석 ID")
    procedure_record = models.ForeignKey(
        ProcedureRecord,
        on_delete=models.CASCADE,
        related_name="preservation_indices",
        verbose_name="시술 기록",
    )
    category_code = models.CharField(max_length=30, verbose_name="카테고리 코드 스냅샷")

    elapsed_days = models.PositiveIntegerField(verbose_name="시술 후 경과일")
    a_d = models.FloatField(verbose_name="A(D) - 오늘 CV 실측치 평균")
    e_d = models.FloatField(verbose_name="E(D) - 기대 감쇠치")
    base_index_value = models.FloatField(verbose_name="기본 보존지수")
    checklist_adjustment = models.IntegerField(verbose_name="체크리스트 보정치")
    final_index_value = models.FloatField(verbose_name="최종 보존지수")

    checklist_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="체크리스트 스냅샷 (더미)",
    )
    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name="산출 일시")

    class Meta:
        db_table = "preservation_index"
        verbose_name = "보존지수"
        verbose_name_plural = "보존지수 목록"
        ordering = ["-calculated_at"]

    def __str__(self):
        return f"[{self.user_id}] record={self.procedure_record_id} analysis={self.analysis_id} score={self.final_index_value}"
