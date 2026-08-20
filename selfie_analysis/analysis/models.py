from django.db import models


# 분석 상태
class AnalysisStatus(models.TextChoices):
    PENDING = "PENDING", "분석 대기/진행 중"
    SUCCESS = "SUCCESS", "분석 성공"
    FAIL = "FAIL", "분석 실패"


class FailReason(models.TextChoices):
    NO_FACE = "NO_FACE", "얼굴 미검출"
    MULTIPLE_FACES = "MULTIPLE_FACES", "다중 얼굴"
    MASK_DETECTED = "MASK_DETECTED", "마스크 착용"
    MOTION_BLUR = "MOTION_BLUR", "흔들림"
    FACE_TOO_SMALL = "FACE_TOO_SMALL", "얼굴 너무 작음"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE", "용량 초과"
    UPLOAD_FAILED = "UPLOAD_FAILED", "업로드 실패"
    API_ERROR = "API_ERROR", "API 오류"



# 셀카 분석
class SelfieAnalysis(models.Model):

    analysis_id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    captured_at = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=AnalysisStatus.choices, default=AnalysisStatus.PENDING
    )
    fail_reason = models.CharField(
        max_length=50, choices=FailReason.choices, null=True, blank=True
    )

    # 폴링/재시도/디버깅을 위한 벤더 호출 추적용. 메인 서버 스키마와는 무관
    provider = models.CharField(max_length=30, null=True, blank=True)
    provider_file_id = models.CharField(max_length=100, null=True, blank=True)
    provider_task_id = models.CharField(max_length=150, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "selfie_analysis"

    def __str__(self):
        return f"SelfieAnalysis(id={self.analysis_id}, status={self.status})"


class SelfieAnalysisDetail(models.Model):
    detail_id = models.BigAutoField(primary_key=True)
    analysis = models.ForeignKey(
        SelfieAnalysis, on_delete=models.CASCADE, related_name="details",
        db_column="analysis_id",
    )
    metric_code = models.CharField(max_length=30)
    metric_value = models.DecimalField(max_digits=6, decimal_places=2)
    metric_unit = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = "selfie_analysis_detail"

    def __str__(self):
        return f"{self.metric_code}={self.metric_value}"
