from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    ForgotPasswordView,
    ResendOtpView, 
    ResetPasswordView, 
    ChangePasswordView,
    UserProfileView,
    VerifyOTPView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/resend-otp/', ResendOtpView.as_view(), name='resend-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/me/', UserProfileView.as_view(), name='user-profile'),
    path('auth/update-profile/', UserProfileView.as_view(), name='update-profile'),

]
