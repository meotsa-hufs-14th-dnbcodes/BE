from rest_framework import serializers

from .models import SelfieAnalysis, SelfieAnalysisDetail


class SelfieUploadSerializer(serializers.Serializer):
    """
    클라이언트가 대칭키로 암호화한 셀카 업로드 요청.
    실제 이미지 바이트는 여기 없다 — encrypted_key/nonce/ciphertext는 모두 base64 문자열.
    (스킴은 analysis.crypto 모듈 docstring 참고)
    """

    user_id = serializers.IntegerField()
    captured_at = serializers.DateTimeField()
    encrypted_key = serializers.CharField()
    nonce = serializers.CharField()
    ciphertext = serializers.CharField()


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
