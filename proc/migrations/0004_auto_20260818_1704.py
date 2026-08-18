from django.db import migrations

def insert_initial_data(apps, schema_editor):
    Category = apps.get_model('proc', 'Category')
    Procedure = apps.get_model('proc', 'Procedure')

    data = [
        {
            "category_name": "리프팅",
            "procedures": [
                {"proc_code": "P001", "proc_name": "울쎄라피 프라임", "proc_duration": 12},
                {"proc_code": "P002", "proc_name": "써마지 FLX", "proc_duration": 12},
                {"proc_code": "P003", "proc_name": "티타늄 리프팅", "proc_duration": 6},
                {"proc_code": "P004", "proc_name": "슈링크 유니버스", "proc_duration": 3},
                {"proc_code": "P005", "proc_name": "인모드", "proc_duration": 6},
                {"proc_code": "P006", "proc_name": "소프웨이브", "proc_duration": 12},
                {"proc_code": "P007", "proc_name": "온다", "proc_duration": 4},
                {"proc_code": "P008", "proc_name": "올타이트", "proc_duration": 6},
            ],
        },
        {
            "category_name": "스킨부스터",
            "procedures": [
                {"proc_code": "P009", "proc_name": "리쥬란", "proc_duration": 2},
                {"proc_code": "P010", "proc_name": "쥬베룩", "proc_duration": 2},
                {"proc_code": "P011", "proc_name": "엑소좀", "proc_duration": 1},
                {"proc_code": "P012", "proc_name": "스킨바이브", "proc_duration": 6},
            ],
        },
        {
            "category_name": "콜라겐 부스터",
            "procedures": [
                {"proc_code": "P013", "proc_name": "스컬트라", "proc_duration": 24},
                {"proc_code": "P014", "proc_name": "엘란쎄", "proc_duration": 18},
                {"proc_code": "P015", "proc_name": "쥬베룩 볼륨", "proc_duration": 12},
            ],
        },
        {
            "category_name": "보톡스",
            "procedures": [
                {"proc_code": "P016", "proc_name": "보톡스", "proc_duration": 6},
            ],
        },
        {
            "category_name": "필러",
            "procedures": [
                {"proc_code": "P017", "proc_name": "필러", "proc_duration": 9},
            ],
        },
        {
            "category_name": "기타",
            "procedures": [
                {"proc_code": "P018", "proc_name": "직접입력", "proc_duration": 0},
            ],
        },
    ]

    for item in data:
        cat, _ = Category.objects.get_or_create(category_name=item["category_name"])
        for proc in item["procedures"]:
            Procedure.objects.update_or_create(
                proc_code=proc["proc_code"],
                defaults={
                    "category": cat,
                    "proc_name": proc["proc_name"],
                    "proc_duration": proc["proc_duration"],
                },
            )

class Migration(migrations.Migration):

    dependencies = [
        ('proc', '0001_initial'),  # 만약 이전 마이그레이션 파일명이 다르면 그 이름으로 적어주세요
    ]

    operations = [
        migrations.RunPython(insert_initial_data),
    ]