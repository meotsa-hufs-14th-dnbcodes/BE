from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proc", "0005_merge_0004_auto_20260818_1704_0004_procedurerecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="procedure",
            name="reminder_duration_days",
            field=models.PositiveIntegerField(
                default=180,
                help_text=( ),
                verbose_name="재시술 알림 기준일수",
            ),
        ),
    ]