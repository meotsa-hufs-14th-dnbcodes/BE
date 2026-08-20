from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("RETREATMENT", "재시술 알림"),
                    ("TODAY_CARE", "오늘의 케어 알림"),
                    ("WEEKLY_REPORT", "주간 보존지수 리포트"),
                    ("ANALYSIS_DONE", "셀카 분석 완료 알림"),
                ],
                max_length=20,
                verbose_name="알림 종류",
            ),
        ),
    ]
