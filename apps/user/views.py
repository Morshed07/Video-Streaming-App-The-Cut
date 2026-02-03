from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .models import User, OtpLog
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    ForgotPasswordSerializer,
    ResetPasswordSerializer, 
    ChangePasswordSerializer,
    UserProfileSerializer,
    UserUpdateSerializer
)
from .utils import get_tokens_for_user, send_otp_email


class BaseAuthView(APIView):

    def get_error_response(self, serializer):
        error_message = list(serializer.errors.values())[0][0]
        if isinstance(error_message, dict): # Handle nested errors
            error_message = list(error_message.values())[0][0]
        return Response({
            "success": False,
            "message": error_message
        }, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(BaseAuthView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return self.get_error_response(serializer)
        user = serializer.save()
        return Response({
            "success": True,
            "message": "User registered successfully.",
            "data": {"email": user.email}
        }, status=status.HTTP_201_CREATED)


class LoginView(BaseAuthView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return self.get_error_response(serializer)
        user = serializer.validated_data['user']
        last_login = timezone.now()
        user.last_login = last_login
        user.save()
        return Response({
            "success": True,
            "message": "Login Success",
            "tokens": get_tokens_for_user(user),
            "user": {"email": user.email, "full_name": user.full_name}
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(BaseAuthView):

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return self.get_error_response(serializer)
        
        user = User.objects.get(email=serializer.validated_data['email'])
        otp_log = OtpLog.objects.filter(user=user).first()
        
        if otp_log and not otp_log.can_resend():
            return Response({
                "success": False, 
                "message": "Please wait before requesting a new code."
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        send_otp_email(user)
        return Response({
            "success": True, 
            "message": "OTP sent to email.", 
            "email": user.email
        }, status=status.HTTP_200_OK)


class ResendOtpView(BaseAuthView):

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return self.get_error_response(serializer)
            
        user = User.objects.get(email=serializer.validated_data['email'])
        otp_log = OtpLog.objects.filter(user=user).first()
        
        if otp_log and not otp_log.can_resend():
            time_left = (otp_log.resend_after - timezone.now()).seconds
            return Response({
                "success": False, 
                "message": f"Wait {time_left} seconds."
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        send_otp_email(user)
        return Response({"success": True, "message": "A new OTP has been sent."}, status=status.HTTP_200_OK)


class ResetPasswordView(BaseAuthView):

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return self.get_error_response(serializer)
        
        user = User.objects.get(email=serializer.validated_data['email'])
        otp_log = OtpLog.objects.filter(user=user).first()
        
        if otp_log and otp_log.verify_otp(serializer.validated_data['otp']):
            user.set_password(serializer.validated_data['password'])
            user.save()
            otp_log.delete()
            return Response({"success": True, "message": "Password reset successful."}, status=status.HTTP_200_OK)
        
        return Response({"success": False, "message": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(BaseAuthView):

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return self.get_error_response(serializer)
            
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"success": False, "message": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['password'])
        user.save()
        return Response({"success": True, "message": "Password changed successfully."}, status=status.HTTP_200_OK)
    

class UserProfileView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.get_error_response(serializer)
        serializer.save()
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)