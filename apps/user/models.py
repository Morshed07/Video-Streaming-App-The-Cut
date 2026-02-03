from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
import random

from apps.core.models import BaseModel


# =========================
# Upload path
# =========================
def user_image_upload_path(instance, filename):
    user_email = instance.email.replace("@", "_")
    return f"{user_email}/profile_image/{filename}"


# =========================
# User Manager
# =========================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email).lower()
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        if kwargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **kwargs)


# =========================
# User Model
# =========================
class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    SUBSCRIPTION_TYPES = (
        ('free', 'Free'),
        ('premium', 'Premium'),
    )

    email = models.EmailField(unique=True, max_length=255)
    full_name = models.CharField(max_length=255, blank=True, null=True)

    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPES,
        default='free'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    kid_mode = models.BooleanField(default=False)

    profile_image = models.ImageField(
        upload_to=user_image_upload_path,
        null=True,
        blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['subscription_type', 'subscription_end_date']),
        ]

    def __str__(self):
        return self.email

    @property
    def is_premium(self):
        return (
            self.subscription_type == 'premium'
            and self.subscription_end_date
            and self.subscription_end_date >= timezone.now()
        )


# =========================
# OTP Model
# =========================
class OtpLog(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_logs'
    )

    otp = models.CharField(max_length=128)  # hashed OTP
    resend_after = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'expires_at']),
        ]

    def generate_otp(self, length=6, resend_seconds=30, expire_minutes=10):
        """
        Generates a new OTP, removes old OTPs,
        stores hashed OTP, and returns raw OTP
        """

        # Remove previous OTPs
        OtpLog.objects.filter(user=self.user).delete()

        raw_otp = ''.join(str(random.randint(0, 9)) for _ in range(length))
        now = timezone.now()

        self.otp = make_password(raw_otp)
        self.resend_after = now + timedelta(seconds=resend_seconds)
        self.expires_at = now + timedelta(minutes=expire_minutes)

        self.save()
        return raw_otp

    def verify_otp(self, input_otp):
        if not self.otp or not self.expires_at:
            return False

        if timezone.now() > self.expires_at:
            return False

        return check_password(input_otp, self.otp)

    def can_resend(self):
        if not self.resend_after:
            return True
        return timezone.now() >= self.resend_after

    def __str__(self):
        return f"OTP for {self.user.email}"
