from django.contrib import admin
from .models import TodayCareRecommendation


@admin.register(TodayCareRecommendation)
class TodayCareRecommendationAdmin(admin.ModelAdmin):
    list_display = ("daily_check", "source", "created_at", "updated_at")
    list_filter = ("source",)

# Register your models here.
