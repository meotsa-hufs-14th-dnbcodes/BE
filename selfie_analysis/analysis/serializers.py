from rest_framework import serializers

from .models import SelfieAnalysis, SelfieAnalysisDetail


class SelfieUploadSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    captured_at = serializers.DateTimeField()


class SelfieAnalysisDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfieAnalysisDetail
        fields = ["metric_code", "metric_value", "metric_unit"]


class SelfieAnalysisSerializer(serializers.ModelSerializer):
    details = SelfieAnalysisDetailSerializer(many=True, read_only=True)

    class Meta:
        model = SelfieAnalysis
        fields = [
            "analysis_id",
            "user_id",
            "captured_at",
            "status",
            "fail_reason",
            "details",
        ]
