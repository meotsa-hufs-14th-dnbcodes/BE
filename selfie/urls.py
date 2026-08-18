from django.urls import path

from .views import SelfieAnalysisCreateView, SelfieAnalysisDetailView, SelfieAnalysisWebhookView

urlpatterns = [
    path('selfie-analyses/', SelfieAnalysisCreateView.as_view(), name='selfie-analysis-create'),
    path('selfie-analyses/<int:analysis_id>/', SelfieAnalysisDetailView.as_view(), name='selfie-analysis-detail'),
    path('selfie-analyses/webhook/', SelfieAnalysisWebhookView.as_view(), name='selfie-analysis-webhook'),

]
