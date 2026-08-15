from rest_framework import serializers
from .models import Category, Procedure

class ProcedureSerializer(serializers.ModelSerializer):
    procCode = serializers.CharField(source='proc_code', read_only=True)
    procName = serializers.CharField(source='proc_name', read_only=True)

    class Meta:
        model = Procedure
        field = ['procCode','procName']

class CategoryProcedureSerializer(serializers.ModelSerializer):
    categoryName = serializers.CharField(source='category_name', read_only=True)
    procedures = ProcedureSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        field = ['categoryName', 'procedures']

    