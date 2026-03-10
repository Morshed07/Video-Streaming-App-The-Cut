from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, OtpLog

# =========================
# Registration
# =========================


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'confirm_password')

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)


# =========================
# Login
# =========================
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email').lower()
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        
        attrs['user'] = user
        return attrs


# =========================
# Forgot Password / Resend OTP
# =========================
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate_email(self, value):
        value = value.lower()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def validate(self, attrs):
        email = attrs.get('email')
        input_otp = attrs.get('otp')

        user = User.objects.get(email=email)
        
        otp_log = OtpLog.objects.filter(user=user).first()

        if not otp_log:
            raise serializers.ValidationError({"otp": "No OTP was requested for this email."})
            
        if otp_log.is_expired:
            raise serializers.ValidationError({"otp": "OTP has expired. Please request a new one."})
            
        if not otp_log.verify_otp(input_otp):
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        attrs['otp_obj'] = otp_log
        return attrs


# =========================
# Reset Password
# =========================
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        email = attrs.get("email")

        if password != confirm_password:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )

        attrs["user"] = user
        return attrs


# =========================
# Change Password (Authenticated)
# =========================
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    

# =========================
# User Profile
# =========================
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'last_login', 'profile_image', 'kid_mode', 'subscription_type')
        read_only_fields = ('email', 'last_login')


# =========================
# Update Profile
# =========================
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('full_name', 'profile_image', 'kid_mode')
        # Ensure fields like email aren't editable here to prevent auth issues
        read_only_fields = ('email', 'subscription_type')

    def validate_full_name(self, value):
        if value and len(value) < 2:
            raise serializers.ValidationError("Full name must be at least 2 characters long.")
        return value
    

# =========================
# Kid Mode Pin Serializer
# =========================


class SetupKidModeSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4, min_length=4)

    def validate_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("PIN must contain only numbers.")
        return value


class ToggleKidModeSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4, min_length=4)


class ChangeKidModePINSerializer(serializers.Serializer):
    old_pin = serializers.CharField(max_length=4, min_length=4)
    new_pin = serializers.CharField(max_length=4, min_length=4)

    def validate(self, data):
        # Ensure both inputs are only digits
        if not data['old_pin'].isdigit() or not data['new_pin'].isdigit():
            raise serializers.ValidationError("PINs must contain only numbers.")
            
        # Prevent changing the PIN to the exact same thing
        if data['old_pin'] == data['new_pin']:
            raise serializers.ValidationError("New PIN cannot be the same as the old PIN.")
            
        return data