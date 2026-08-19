from rest_framework import serializers
from .models import DailyCheck

# -------------------------------------------------------------
# 1. 오늘의 체크리스트 등록 (POST /checklist/checklist) Serializers
# -------------------------------------------------------------
class DailyCheckCreateRequestSerializer(serializers.ModelSerializer):
    uvProtectionYn = serializers.BooleanField(source='uv_protection_yn')
    regenCreamYn = serializers.BooleanField(source='regen_cream_yn')
    drinkingYn = serializers.BooleanField(source='drinking_yn')
    smokingYn = serializers.BooleanField(source='smoking_yn')
    intenseExerciseYn = serializers.BooleanField(source='intense_exercise_yn')

    class Meta:
        model = DailyCheck
        fields = [
            'uvProtectionYn',
            'regenCreamYn',
            'drinkingYn',
            'smokingYn',
            'intenseExerciseYn'
        ]


class DailyCheckCreateResponseSerializer(serializers.ModelSerializer):
    checklistId = serializers.IntegerField(source='checklist_id')
    userId = serializers.IntegerField(source='user_id')
    checkDate = serializers.DateField(source='check_date')
    isCompleted = serializers.SerializerMethodField()

    class Meta:
        model = DailyCheck
        fields = ['checklistId', 'userId', 'checkDate', 'isCompleted']

    def get_isCompleted(self, obj):
        return True


# -------------------------------------------------------------
# 2. 주간 체크리스트 현황 조회 (GET /checklist/weeklyChecklist) Serializers
# -------------------------------------------------------------
class WeeklyRecordItemSerializer(serializers.Serializer):
    dayOrder = serializers.IntegerField()
    date = serializers.CharField()
    isChecked = serializers.BooleanField()
    isToday = serializers.BooleanField()


class WeeklyChecklistResponseSerializer(serializers.Serializer):
    currentDay = serializers.IntegerField()
    isChecklistDone = serializers.BooleanField()
    weeklyRecords = WeeklyRecordItemSerializer(many=True)