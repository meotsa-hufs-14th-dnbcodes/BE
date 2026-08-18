from django.urls import path

from .views import SelfieAnalysisCreateView, SelfieAnalysisDetailView

app_name = "analysis"

urlpatterns = [
    path("selfie-analyses/", SelfieAnalysisCreateView.as_view(), name="create"),
    path(
        "selfie-analyses/<int:analysis_id>/",
        SelfieAnalysisDetailView.as_view(),
        name="detail",
    ),
]
