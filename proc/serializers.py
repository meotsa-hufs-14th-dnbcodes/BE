from rest_framework import serializers
from .models import Category, Procedure, ProcedureRecord
from datetime import date

class ProcedureSerializer(serializers.ModelSerializer):
    procCode = serializers.CharField(source='proc_code', read_only=True)
    procName = serializers.CharField(source='proc_name', read_only=True)

    class Meta:
        model = Procedure
        fields = ['procCode','procName']

class CategoryProcedureSerializer(serializers.ModelSerializer):
    categoryName = serializers.CharField(source='category_name', read_only=True)
    procedures = ProcedureSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['categoryName', 'procedures']

class ProcedureRecordCreateSerializer(serializers.ModelSerializer):
    procName = serializers.CharField(source='proc_name', max_length=100)
    procedureDate = serializers.DateField(source='procedure_date')
    hospitalName = serializers.CharField(source='hospital_name', required=False, allow_blank=True, allow_null=True, max_length=50)
    memo = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=500)
    duplicateConfirm = serializers.BooleanField(write_only=True, required=False, default=False)

    recordId = serializers.IntegerField(source='record', read_only=True)
    userId = serializers.IntegerField(source='user_id', read_only=True)
    categoryId = serializers.IntegerField(source='procedure.category_id', read_only=True)
    procCode = serializers.CharField(source='procedure.proc_code', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%dT%H:%M:%S', read_only=True)
    isDeleted = serializers.BooleanField(source='is_deleted', read_only=True)

    class Meta:
        model = ProcedureRecord
        fields = [
            'recordId',
            'userId',
            'categoryId',
            'procCode',
            'procName',
            'procedureDate',
            'hospitalName',
            'memo',
            'duplicateConfirm',
            'createdAt',
            'isDeleted',
        ]

    def validate_procedureDate(self, value):
        if value > date.today():
            raise serializers.ValidationError("시술 날짜는 오늘 이후의 날짜로 등록할 수 없습니다.")
        return value

    def validate(self, attrs):
        # PATCH 등 부분 수정에서 procName을 안 보낸 경우, 기존에 연결된
        # Procedure를 그대로 유지한다 (재조회하지 않음).
        if 'proc_name' not in attrs:
            if self.instance is not None:
                attrs['procedure'] = self.instance.procedure
                return attrs
            proc_name = ''
        else:
            proc_name = attrs.get('proc_name', '').strip()

        procedure = Procedure.objects.filter(proc_name=proc_name).first()

        if not procedure:
            try:
                procedure = Procedure.objects.get(proc_code='P018')
            except Procedure.DoesNotExist:
                raise serializers.ValidationError({"procName": "기본 시술 정보(기타: P018)가 존재하지 않습니다."})

        attrs['procedure'] = procedure
        return attrs

    def create(self, validated_data):
        validated_data.pop('duplicateConfirm', None)

        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('duplicateConfirm', None)
        return super().update(instance, validated_data)


class ProcedureRecordDateSerializer(serializers.ModelSerializer):
    procName = serializers.CharField(source='proc_name', read_only=True)
    procedureDate = serializers.DateField(source='procedure_date', read_only=True)
    hospitalName = serializers.CharField(source='hospital_name', read_only=True)

    class Meta:
        model = ProcedureRecord
        fields = ['procName', 'procedureDate', 'hospitalName']
