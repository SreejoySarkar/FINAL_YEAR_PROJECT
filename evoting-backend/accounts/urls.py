from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminLoginView,
    AdminLogoutView,
    AdminVerifyOTPView,
)

urlpatterns = [
    path("admin/login", AdminLoginView.as_view()),
    path("admin/verify-otp", AdminVerifyOTPView.as_view()),
    path("admin/logout", AdminLogoutView.as_view()),
    path("admin/token/refresh", TokenRefreshView.as_view()),
]