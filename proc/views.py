from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category
from .serializers import CategoryProcedureSerializer

class CategoryProcedureListView(APIView):
    def get(self, request):
        categories = Category.objects.prefetch_related('procedures').all()
        serializer = CategoryProcedureSerializer(categories, many=True)

        response_data = {
            "status": 200,
            "data": serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)