from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import NotFound
from .models import Category, ProcedureRecord
from .serializers import CategoryProcedureSerializer, ProcedureRecordCreateSerializer
from rest_framework.permissions import IsAuthenticated

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

    def get_queryset(self):
        return ProcedureRecord.objects.filter(
            user=self.request.user, 
            is_deleted=False
        ).select_related('procedure__category')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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


class ProcedureRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    마이페이지 > 시술 이력 관리에서 사용하는 단건 조회/수정/삭제 뷰.
    - 삭제는 실제로 row를 지우지 않고 is_deleted=True로 처리하는 소프트 삭제 방식이다.
      (notifications/care/preservation 등 다른 도메인이 이미 is_deleted=False를
      기준으로 조회하고 있고, PreservationIndex가 ProcedureRecord를 CASCADE로 물고 있어서
      하드 삭제 시 재시술 알림·케어·보존지수 이력까지 함께 사라지는 것을 막기 위함)
    - 수정은 procName / procedureDate / hospitalName / memo를 부분 수정(PATCH)
      또는 전체 수정(PUT) 할 수 있다. procName을 바꾸지 않으면 기존에 연결된
      시술 코드가 그대로 유지된다.
    """
    serializer_class = ProcedureRecordCreateSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'record_id'
    lookup_field = 'record'

    def get_queryset(self):
        return ProcedureRecord.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('procedure__category')

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise NotFound("해당 시술 기록을 찾을 수 없거나 이미 삭제되었습니다.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {
                "message": "시술 기록이 수정되었습니다.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "message": "시술 기록이 삭제되었습니다.",
                "data": {"recordId": instance.record}
            },
            status=status.HTTP_200_OK
        )