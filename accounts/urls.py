from django.urls import path

from .views import LoginView, MyPageView, SignupView

urlpatterns = [
    path("signup", SignupView.as_view(), name="signup"),
    path("login", LoginView.as_view(), name="login"),
    path("mypage", MyPageView.as_view(), name="mypage"),
]