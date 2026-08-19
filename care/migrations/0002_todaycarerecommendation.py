import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checklist", "0001_initial"),
        ("care", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TodayCareRecommendation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("summary", models.CharField(max_length=250, verbose_name="오늘의 케어 요약")),
                ("items", models.JSONField(default=list, verbose_name="추천 Action 목록")),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("llm", "OpenAI 생성"),
                            ("llm_error", "OpenAI 오류 (카탈로그 원문 대체)"),
                            ("default_routine", "추천 Action 없음 - 기본 루틴"),
                        ],
                        max_length=20,
                        verbose_name="생성 방식",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "daily_check",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="care_recommendation",
                        to="checklist.dailycheck",
                        verbose_name="연결된 데일리 체크리스트",
                    ),
                ),
            ],
            options={
                "verbose_name": "오늘의 케어 추천",
                "verbose_name_plural": "오늘의 케어 추천 목록",
                "db_table": "today_care_recommendation",
            },
        ),
    ]