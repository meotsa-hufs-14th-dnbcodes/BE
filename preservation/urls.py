from django.urls import path

from .views import PreservationIndexListCreateView

urlpatterns = [
    path("indices/", PreservationIndexListCreateView.as_view(), name="preservation-index-list-create"),
]
