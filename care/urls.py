from django.urls import path
from .views import ProductRecommendationView, TodayCareView

urlpatterns = [
    path('products/', ProductRecommendationView.as_view(), name='product-recommendations'),
    path('today/', TodayCareView.as_view(), name='care-today'),
]