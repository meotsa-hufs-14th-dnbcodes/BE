from django.db import models
from django.conf import settings

class Category(models.Model):
    category_name = models.CharField(max_length=20, verbose_name="카테고리명")

    def __str__(self):
        return self.category_name

class Procedure(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="procedures",
        verbose_name="카테고리"
    )
    proc_code = models.CharField(max_length=20, primary_key=True, verbose_name="시술 코드")
    proc_name = models.CharField(max_length=50, verbose_name="시술명")
    proc_duration = models.PositiveIntegerField(
        help_text="지속 기간(개월 단위, 예: 1, 6, 12)",
        verbose_name="지속기간(개월)"
    )
    reminder_duration_days = models.PositiveIntegerField(
        default=180,
        help_text=(
            "재시술 알림 계산 전용 필드(일 단위). 기획서 '기준 지속기간'이 범위값"
            "(예: 4~6주, 9~12개월)인 경우 짧은 쪽(최솟값)을 일수로 환산해 저장한다."
            "보존지수 감쇠 계산에 쓰는 proc_duration(개월)과는 별개 필드다."
        ),
        verbose_name="재시술 알림 기준일수",
    )

    def __str__(self):
        return f"[{self.proc_code}] {self.proc_name} ({self.proc_duration}개월)"

class ProcedureRecord(models.Model):
    record = models.BigAutoField(primary_key=True, verbose_name="기록 ID")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="procedure_records",
        verbose_name="사용자"
    )

    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.PROTECT,
        db_column="proc_code",
        related_name="records",
        verbose_name="시술 코드",
    )

    proc_name = models.CharField(max_length=100, verbose_name="시술명")

    procedure_date = models.DateField(verbose_name="시술 날짜")
    hospital_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="병원명")
    memo = models.TextField(null=True, blank=True, verbose_name="시술 관련 메모")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록 일시")
    is_deleted = models.BooleanField(default=False, verbose_name="삭제 여부")

    class Meta:
        db_table = "procedure_record"
        verbose_name = "시술 기록"
        verbose_name_plural = "시술 기록 목록"
        ordering = ["-procedure_date", "-created_at"]

    def __str__(self):
        return f"[{self.user_id}] {self.proc_name} ({self.procedure_date})"
