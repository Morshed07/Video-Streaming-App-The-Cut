from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.category.models import (
    Category,
    Tag
)

# Create your models here.

User = settings.AUTH_USER_MODEL


def user_video_upload_path(instance, filename):
    user_email = instance.email.replace("@", "_")
    return f"{user_email}/videos/{filename}"


class Video(BaseModel):
    KIDS_AGE_RATINGS = [
        ('6+', '6+'),
        ('10+', '10+'),
        ('14+', '14+'),
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