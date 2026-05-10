from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.category.models import (
    Category,
    Tag
)
from datetime import timedelta

# Create your models here.

User = settings.AUTH_USER_MODEL


def user_video_upload_path(instance, filename):
    if instance.upload_by:
        user_email = instance.upload_by.email.replace("@", "_")
        return f"{user_email}/videos/{filename}"
    return f"videos/{filename}"


class Video(BaseModel):
    KIDS_AGE_RATINGS = [
        ('6+', '6+'),
        ('10+', '10+'),
        ('14+', '14+'),
    ]

    UPLOAD_STATUS_CHOICES = [
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('needs_changes', 'Needs Changes'),
            ('flagged', 'Flagged for Review'),
            ('festival', 'Festival')
        ]
    upload_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_videos')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    
    # Media files
    video_file = models.FileField(upload_to=user_video_upload_path)
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/')
    
    # Video metadata
    duration = models.DurationField(help_text="Video duration")
    age_rating = models.CharField(max_length=10, choices=KIDS_AGE_RATINGS, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default='pending')
    # Categories and classification
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='videos')
    tags = models.ManyToManyField(Tag, blank=True, related_name='videos')
    
    # Engagement metrics
    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_kids_friendly = models.BooleanField(default=False)
    
    #Aws 
    hls_url = models.URLField(null=True, blank=True)         # master playlist
    hls_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('ready', 'Ready'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    hls_job_id = models.CharField(max_length=255, null=True, blank=True)  # MediaConvert job ID

    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['is_published', '-published_at']),
            models.Index(fields=['is_trending']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.title.lower().replace(' ', '-')
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

    @property
    def duration_display(self):
        #Format duration as HH:MM:SS
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    

class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='watch_history')
    watch_duration = models.DurationField(default=timedelta(seconds=0), null=True, blank=True)
    last_watched_position = models.DurationField(default=timedelta(seconds=0), null=True, blank=True)
    completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)
    first_watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video']
        ordering = ['-last_watched_at']
        verbose_name_plural = "Watch histories"
        indexes = [
            models.Index(fields=['user', '-last_watched_at']),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.video.title}"

    @property
    def progress_percentage(self):
        """Calculate watch progress percentage"""
        if self.video.duration.total_seconds() > 0:
            progress = (self.last_watched_position.total_seconds() / 
                       self.video.duration.total_seconds()) * 100
            return min(progress, 100)
        return 0


class Favorite(models.Model):
    """User's favorite/liked videos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"

