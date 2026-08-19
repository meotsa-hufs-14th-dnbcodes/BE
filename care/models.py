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
