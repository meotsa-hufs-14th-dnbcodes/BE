from django.db import models
from proc.models import Category

class Product(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    tags = models.JSONField(default=list, help_text="['진정', '수분'] 형태의 태그 목록")
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class CategoryProductMapping(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='product_mappings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='category_mappings')

    class Meta:
        unique_together = ('category', 'product')


class TodayCareRecommendation(models.Model):

    #LLM은 하루에 한번(셀카 등록 시에만) 호출
    
    SOURCE_LLM = "llm"
    SOURCE_LLM_ERROR = "llm_error"
    SOURCE_DEFAULT_ROUTINE = "default_routine"
    SOURCE_CHOICES = [
        (SOURCE_LLM, "OpenAI 생성"),
        (SOURCE_LLM_ERROR, "OpenAI 오류 (카탈로그 원문 대체)"),
        (SOURCE_DEFAULT_ROUTINE, "추천 Action 없음 - 기본 루틴"),
    ]

    daily_check = models.OneToOneField(
        "checklist.DailyCheck",
        on_delete=models.CASCADE,
        related_name="care_recommendation",
        verbose_name="연결된 데일리 체크리스트",
    )
    summary = models.CharField(max_length=250, verbose_name="오늘의 케어 요약")
    items = models.JSONField(default=list, verbose_name="추천 Action 목록")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, verbose_name="생성 방식")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "today_care_recommendation"
        verbose_name = "오늘의 케어 추천"
        verbose_name_plural = "오늘의 케어 추천 목록"

    def __str__(self):
        return f"{self.daily_check} - {self.source}"