from django.db import models
from django.conf import settings
from apps.core.models import BaseModel

User = settings.AUTH_USER_MODEL


class Notification(BaseModel):
    NOTIFICATION_TYPES = [
        ('video_published', 'Video Published'),
        ('video_liked', 'Video Liked'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Related objects
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_notifications', help_text="User who triggered the notification (e.g., who liked the video)")
    video = models.ForeignKey('video.Video', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.get_notification_type_display()}"
