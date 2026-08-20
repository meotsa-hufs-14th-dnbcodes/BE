from django.db import models
from django.conf import settings


class PendingPreservationCalc(models.Model):
    """셀카 분석은 성공했는데 그날 체크리스트가 아직 없어서 보존지수 계산을 미룬 상태.
    체크리스트가 등록되면 checklist 앱이 이걸 찾아 계산을 마저 진행하고 지운다."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pending_preservation_calcs",
    )
    analysis_id = models.PositiveIntegerField()
    check_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "check_date")
