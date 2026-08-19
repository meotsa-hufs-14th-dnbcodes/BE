from django.urls import path
from .views import ProductRecommendationView

urlpatterns = [
    path('products/', ProductRecommendationView.as_view(), name='product-recommendations'),
]