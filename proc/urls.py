from django.urls import path
from .views import CategoryProcedureListView, ProcedureRecordCreateView

urlpatterns = [
    path('list/', CategoryProcedureListView.as_view(), name='category-procedure-list'),
    path('records/', ProcedureRecordCreateView.as_view(), name='procedure-record-list-create')
]