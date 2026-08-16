from django.contrib import admin

from .models import SelfieAnalysis, SelfieAnalysisDetail


class SelfieAnalysisDetailInline(admin.TabularInline):
    model = SelfieAnalysisDetail
    extra = 0
    readonly_fields = ["face_part_code", "metric_code", "metric_value", "metric_unit"]
    can_delete = False


@admin.register(SelfieAnalysis)
class SelfieAnalysisAdmin(admin.ModelAdmin):
    list_display = ["analysis_id", "user_id", "captured_at", "status", "fail_reason", "provider"]
    list_filter = ["status", "fail_reason", "provider"]
    inlines = [SelfieAnalysisDetailInline]
