from django.db import models
from apps.core.models import BaseModel
from django.contrib.auth import get_user_model
from apps.video.models import Video

# Create your models here.

User = get_user_model()


class Award(BaseModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title
    

class VideoAward(BaseModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='awards')
    award = models.ForeignKey(Award, on_delete=models.CASCADE, related_name='video_awards')
    awarded_date = models.DateField(auto_now_add=True)
    rank = models.IntegerField(null=True, blank=True, help_text='Ranking if applicable (1st, 2nd, 3rd)')
    
    class Meta:
        unique_together = ['video', 'award']
        ordering = ['awarded_date']

    def __str__(self):
        return f"{self.award.title} - {self.video.title}"


class AwardVote(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='award_votes')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='award_votes')
    award = models.ForeignKey(Award, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video', 'award']
        indexes = [
            models.Index(fields=['video', 'award']),
        ]

    def __str__(self):
        return f"{self.user.username} voted for {self.video.title} - {self.award.title}"