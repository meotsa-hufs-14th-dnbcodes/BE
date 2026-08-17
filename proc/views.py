from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Category, ProcedureRecord
from .serializers import CategoryProcedureSerializer, ProcedureRecordCreateSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class CategoryProcedureListView(APIView):
    def get(self, request):
        categories = Category.objects.prefetch_related('procedures').all()
        serializer = CategoryProcedureSerializer(categories, many=True)

        response_data = {
            "status": 200,
            "data": serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)

class ProcedureRecordCreateView(generics.ListCreateAPIView):
    serializer_class = ProcedureRecordCreateSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return ProcedureRecord.objects.filter(
            user=self.request.user, 
            is_deleted=False
        ).select_related('procedure')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "시술 기록이 성공적으로 등록되었습니다.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )