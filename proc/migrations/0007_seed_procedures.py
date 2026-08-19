from django.db import migrations

# (카테고리명, [ (proc_code, proc_name, proc_duration_months, reminder_duration_days), ... ])
# reminder_duration_days: 범위값은 최솟값 기준으로 환산 (1개월=30일, 1주=7일)
CATEGORY_ORDER = ["리프팅", "스킨부스터", "콜라겐 부스터", "보톡스", "필러", "기타"]

PROCEDURES = [
    ("P001", "울쎄라피 프라임", "리프팅", 12, 360),
    ("P002", "써마지 FLX", "리프팅", 12, 360),
    ("P003", "티타늄 리프팅", "리프팅", 6, 180),
    ("P004", "슈링크 유니버스", "리프팅", 3, 90),
    ("P005", "인모드", "리프팅", 6, 180),
    ("P006", "소프웨이브", "리프팅", 12, 360),
    ("P007", "온다", "리프팅", 6, 180),
    ("P008", "올타이트", "리프팅", 6, 180),
    ("P009", "리쥬란", "스킨부스터", 1, 28),   # 4~6주 -> 최솟값 4주
    ("P010", "쥬베룩", "스킨부스터", 1, 28),   # 4~6주 -> 최솟값 4주
    ("P011", "엑소좀", "스킨부스터", 1, 28),   # 4주
    ("P012", "스킨바이브", "스킨부스터", 6, 180),
    ("P013", "스컬트라", "콜라겐 부스터", 24, 720),
    ("P014", "엘란쎄", "콜라겐 부스터", 18, 540),
    ("P015", "쥬베룩 볼륨", "콜라겐 부스터", 12, 360),
    ("P016", "보톡스", "보톡스", 3, 90),        # 3~4개월 -> 최솟값 3개월
    ("P017", "필러", "필러", 9, 270),           # 9~12개월 -> 최솟값 9개월
    ("P018", "기타", "기타", 6, 180),           # proc/serializers.py 기본 폴백용
]


def seed_categories_and_procedures(apps, schema_editor):
    Category = apps.get_model("proc", "Category")
    Procedure = apps.get_model("proc", "Procedure")

    category_by_name = {}
    for name in CATEGORY_ORDER:
        category = Category.objects.filter(category_name=name).first()
        if category is None:
            category = Category.objects.create(category_name=name)
        category_by_name[name] = category

    for proc_code, proc_name, category_name, duration_months, reminder_days in PROCEDURES:
        Procedure.objects.update_or_create(
            proc_code=proc_code,
            defaults={
                "proc_name": proc_name,
                "category": category_by_name[category_name],
                "proc_duration": duration_months,
                "reminder_duration_days": reminder_days,
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("proc", "0006_procedure_reminder_duration_days"),
    ]

    operations = [
        migrations.RunPython(seed_categories_and_procedures, noop_reverse),
    ]