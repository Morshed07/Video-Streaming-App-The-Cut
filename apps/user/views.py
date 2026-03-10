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
    UserUpdateSerializer,
    VerifyOTPSerializer,
    SetupKidModeSerializer,
    ToggleKidModeSerializer,
    ChangeKidModePINSerializer
)
from .utils import get_tokens_for_user, send_otp_email
from rest_framework.permissions import IsAuthenticated

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
    permission_classes = [permissions.AllowAny]

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
    

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)

        if serializer.is_valid():
            otp_obj = serializer.validated_data["otp_obj"]

            # mark otp as used
            # otp_obj.is_used = True
            otp_obj.save()
            otp_obj.delete()

            return Response(
                {"message": "OTP verified successfully."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(password)
        user.save()

        return Response(
            {
                "success": True,
                "message": "Password reset successful."
            },
            status=status.HTTP_200_OK
        )


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
    

class SetupKidModeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # If user already has a PIN, they shouldn't use the setup endpoint
        if user.kid_mode_pin:
            return Response(
                {"error": "Kid mode PIN is already set. Please use the toggle endpoint."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SetupKidModeSerializer(data=request.data)
        if serializer.is_valid():
            pin = serializer.validated_data['pin']
            
            # Set the hashed PIN and activate kid mode
            user.set_kid_pin(pin)
            user.kid_mode = True
            user.save()
            
            return Response(
                {"message": "Kid mode activated successfully.", "kid_mode": True},
                status=status.HTTP_200_OK
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ToggleKidModeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Ensure the user has actually set up a PIN first
        if not user.kid_mode_pin:
            return Response(
                {"error": "Kid mode PIN has not been set up yet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ToggleKidModeSerializer(data=request.data)
        if serializer.is_valid():
            pin = serializer.validated_data['pin']
            
            # Verify the PIN
            if not user.check_kid_pin(pin):
                return Response(
                    {"error": "Incorrect PIN."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Toggle the boolean state
            user.kid_mode = not user.kid_mode
            user.save()
            
            mode_status = "Kid Mode" if user.kid_mode else "Adult Mode"
            return Response(
                {"message": f"Successfully switched to {mode_status}.", "kid_mode": user.kid_mode},
                status=status.HTTP_200_OK
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ChangeKidModePINAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Guard clause: Ensure the user actually has a PIN to change
        if not user.kid_mode_pin:
            return Response(
                {"error": "Kid mode PIN has not been set up yet. Please set it up first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ChangeKidModePINSerializer(data=request.data)
        if serializer.is_valid():
            old_pin = serializer.validated_data['old_pin']
            new_pin = serializer.validated_data['new_pin']
            
            # Verify that the old PIN provided is correct
            if not user.check_kid_pin(old_pin):
                return Response(
                    {"error": "Incorrect current PIN."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Set the new PIN and save
            user.set_kid_pin(new_pin)
            user.save()
            
            return Response(
                {"message": "Successfully changed Kid Mode Key."},
                status=status.HTTP_200_OK
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)