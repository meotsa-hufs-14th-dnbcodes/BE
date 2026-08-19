from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from proc.models import ProcedureRecord
from checklist.models import DailyCheck
from .models import Product, CategoryProductMapping
from .serializers import RecommendedProductSerializer

PRODUCT_CORE_REBUILD = 1
PRODUCT_HYDRO_SOOTHING = 2
PRODUCT_REPAIR_SOLUTION = 3
PRODUCT_CLARIFY_TONER = 4
PRODUCT_SUN_ESSENCE = 5


class ProductRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = date.today()

        latest_record = ProcedureRecord.objects.filter(
            user=user, 
            is_deleted=False
        ).select_related('procedure__category').order_by('-procedure_date', '-created_at').first()

        if not latest_record or not latest_record.procedure or not latest_record.procedure.category:
            return Response({
                "isSuccess": True,
                "code": "SUCCESS",
                "message": "시술 기록이 없어 추천 제품이 없습니다.",
                "data": []
            }, status=status.HTTP_200_OK)

        category = latest_record.procedure.category

        candidate_products = Product.objects.filter(category_mappings__category=category).distinct()
        if not candidate_products.exists():
            return Response({
                "isSuccess": True,
                "code": "SUCCESS",
                "message": "해당 시술에 매칭된 제품이 없습니다.",
                "data": []
            }, status=status.HTTP_200_OK)

        product_scores = {p.id: 0 for p in candidate_products}

        def add_score(target_name, score=1):
            for p in candidate_products:
                if p.name.strip() == target_name:
                    product_scores[p.id] += score

        days_after_procedure = (today - latest_record.procedure_date).days + 1
        if 1 <= days_after_procedure <= 7:
            add_score(PRODUCT_REPAIR_SOLUTION, 3)

        today_check = DailyCheck.objects.filter(user=user, check_date=today).first()
        if today_check:
            if getattr(today_check, 'drank_alcohol', False) or getattr(today_check, 'heavy_exercise', False):
                add_score(PRODUCT_HYDRO_SOOTHING, 2)

            if getattr(today_check, 'heavy_exercise', False):
                add_score(PRODUCT_CLARIFY_TONER, 2)

            if not getattr(today_check, 'applied_cream', False) or getattr(today_check, 'smoked', False):
                add_score(PRODUCT_CORE_REBUILD, 2)

            if not getattr(today_check, 'used_sunscreen', False):
                add_score(PRODUCT_SUN_ESSENCE, 2)

        sorted_products = sorted(
            candidate_products,
            key=lambda p: product_scores.get(p.id, 0),
            reverse=True
        )
        recommended = sorted_products[:2]

        serializer = RecommendedProductSerializer(recommended, many=True, context={'request': request})
        return Response({
            "isSuccess": True,
            "code": "SUCCESS",
            "message": "추천 제품 목록 조회가 완료되었습니다.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)