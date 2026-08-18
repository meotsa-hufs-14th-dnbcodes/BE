from django.urls import path

from .views import PerfectCorpWebhookView, SelfieAnalysisCreateView, SelfieAnalysisDetailView

app_name = "analysis"

urlpatterns = [
    path("selfie-analyses/", SelfieAnalysisCreateView.as_view(), name="create"),
    path(
        "selfie-analyses/<int:analysis_id>/",
        SelfieAnalysisDetailView.as_view(),
        name="detail",
    ),
    path("webhooks/perfectcorp/", PerfectCorpWebhookView.as_view(), name="perfectcorp-webhook"),
]
