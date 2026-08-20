import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "notification_type",
                    models.CharField(
                        choices=[
                            ("RETREATMENT", "재시술 알림"),
                            ("TODAY_CARE", "오늘의 케어 알림"),
                            ("WEEKLY_REPORT", "주간 보존지수 리포트"),
                        ],
                        max_length=20,
                        verbose_name="알림 종류",
                    ),
                ),
                ("title", models.CharField(max_length=100, verbose_name="제목")),
                ("body", models.CharField(max_length=255, verbose_name="본문")),
                ("dedupe_key", models.CharField(max_length=150, verbose_name="중복 생성 방지 키")),
                ("payload", models.JSONField(blank=True, default=dict, verbose_name="부가 데이터")),
                ("is_read", models.BooleanField(default=False, verbose_name="읽음 여부")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="생성 일시")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="사용자",
                    ),
                ),
            ],
            options={
                "verbose_name": "알림",
                "verbose_name_plural": "알림 목록",
                "db_table": "notification",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["user", "notification_type", "created_at"], name="notif_user_type_created_idx"),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(fields=("user", "dedupe_key"), name="uniq_notification_user_dedupe_key"),
        ),
    ]