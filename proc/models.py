from django.db import models

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

    def __str__(self):
        return f"[{self.proc_code}] {self.proc_name} ({self.proc_duration}개월)"
