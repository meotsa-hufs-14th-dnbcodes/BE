from django.conf import settings
from django.db import models


class Notification(models.Model):
   
    TYPE_RETREATMENT = "RETREATMENT"
    TYPE_TODAY_CARE = "TODAY_CARE"
    TYPE_WEEKLY_REPORT = "WEEKLY_REPORT"
    TYPE_CHOICES = [
        (TYPE_RETREATMENT, "재시술 알림"),
        (TYPE_TODAY_CARE, "오늘의 케어 알림"),
        (TYPE_WEEKLY_REPORT, "주간 보존지수 리포트"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="사용자",
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="알림 종류")
    title = models.CharField(max_length=100, verbose_name="제목")
    body = models.CharField(max_length=255, verbose_name="본문")
    dedupe_key = models.CharField(max_length=150, verbose_name="중복 생성 방지 키")
    payload = models.JSONField(default=dict, blank=True, verbose_name="부가 데이터")
    is_read = models.BooleanField(default=False, verbose_name="읽음 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 일시")

    class Meta:
        db_table = "notification"
        verbose_name = "알림"
        verbose_name_plural = "알림 목록"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "dedupe_key"], name="uniq_notification_user_dedupe_key"),
        ]
        indexes = [
            models.Index(fields=["user", "notification_type", "created_at"], name="notif_user_type_created_idx"),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} (user={self.user_id})"