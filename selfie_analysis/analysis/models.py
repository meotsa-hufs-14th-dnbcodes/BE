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
    provider_task_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "selfie_analysis"

    def __str__(self):
        return f"SelfieAnalysis(id={self.analysis_id}, status={self.status})"


class SelfieAnalysisDetail(models.Model):
    """
    ERD: selfie_analysis_detail (셀카분석상세)
    벤더 응답의 output 배열(region/type/score)을 거의 1:1로 저장한다.
    face_part_code/metric_code는 현재 벤더(API) 원본 코드 그대로이며, 서비스 공통 코드로의
    매핑은 미확정 상태다(기획 문서 기준).
    """

    detail_id = models.BigAutoField(primary_key=True)
    analysis = models.ForeignKey(
        SelfieAnalysis, on_delete=models.CASCADE, related_name="details",
        db_column="analysis_id",
    )
    face_part_code = models.CharField(max_length=30)
    metric_code = models.CharField(max_length=30)
    metric_value = models.DecimalField(max_digits=6, decimal_places=2)
    metric_unit = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = "selfie_analysis_detail"

    def __str__(self):
        return f"{self.face_part_code}/{self.metric_code}={self.metric_value}"
