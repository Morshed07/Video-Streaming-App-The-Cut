from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.video.models import Video, Favorite
from .models import Notification


@receiver(pre_save, sender=Video)
def track_video_publication(sender, instance, **kwargs):
    """
    Track if is_published changes from False to True.
    We use pre_save to compare old and new values.
    """
    if instance.pk:  # Only if the video already exists (not new)
        try:
            old_instance = Video.objects.get(pk=instance.pk)
            # Store the old state in the instance for use in post_save
            instance._was_published = old_instance.is_published
        except Video.DoesNotExist:
            instance._was_published = False
    else:
        instance._was_published = False


@receiver(post_save, sender=Video)
def send_publish_notification(sender, instance, created, **kwargs):
    """
    Send notification to the uploader when their video is published.
    Only triggers when is_published changes from False to True.
    """
    if not created and instance.upload_by:
        # Check if video was just published
        was_published = getattr(instance, '_was_published', False)
        
        if not was_published and instance.is_published:
            # Video just got published
            Notification.objects.create(
                user=instance.upload_by,
                notification_type='video_published',
                title='Your video is published!',
                message=f'Your video "{instance.title}" has been published and is now visible to the public.',
                video=instance,
            )


@receiver(post_save, sender=Favorite)
def send_like_notification(sender, instance, created, **kwargs):
    """
    Send notification to the video uploader when someone likes their video.
    Only triggers when a new favorite is created.
    """
    if created and instance.video.upload_by:
        # Get the liker's name
        liker_name = instance.user.full_name or instance.user.username
        
        Notification.objects.create(
            user=instance.video.upload_by,  # Notify the video uploader
            notification_type='video_liked',
            title='Your video was liked!',
            message=f'{liker_name} liked your video "{instance.video.title}".',
            actor=instance.user,  # The user who liked the video
            video=instance.video,
        )