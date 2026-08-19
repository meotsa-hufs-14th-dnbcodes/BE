from django.urls import path
from .views import ChecklistAPIView, WeeklyChecklistAPIView

urlpatterns = [
    path('checklist/', ChecklistAPIView.as_view(), name='daily-checklist'),
    path('weeklyChecklist/', WeeklyChecklistAPIView.as_view(), name='weekly-checklist'),
]