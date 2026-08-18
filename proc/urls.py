from django.urls import path
from .views import CategoryProcedureListView

urlpatterns = [
    path('list/', CategoryProcedureListView.as_view(), name='category-procedure-list')
]