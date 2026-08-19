from django.db import models
from django.conf import settings

class DailyCheck(models.Model):
    checklist_id = models.BigAutoField(
        primary_key=True, 
        verbose_name="체크리스트 ID"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_checks",
        db_column="user_id",
        verbose_name="사용자 ID"
    )
    check_date = models.DateField(
        verbose_name="체크 일자"
    )
    uv_protection_yn = models.BooleanField(
        default=False, 
        verbose_name="자외선 차단제 사용 여부"
    )
    regen_cream_yn = models.BooleanField(
        default=False, 
        verbose_name="재생크림 사용 여부"
    )
    smoking_yn = models.BooleanField(
        default=False, 
        verbose_name="흡연 여부"
    )
    drinking_yn = models.BooleanField(
        default=False, 
        verbose_name="음주 여부"
    )
    intense_exercise_yn = models.BooleanField(
        default=False, 
        verbose_name="격한 운동 여부"
    )

    class Meta:
        db_table = "dailycheck"
        verbose_name = "데일리 체크리스트"
        verbose_name_plural = "데일리 체크리스트 목록"
        unique_together = ("user", "check_date")

    def __str__(self):
        return f"User {self.user_id} - {self.check_date}"
