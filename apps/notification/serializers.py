from rest_framework import serializers
from .models import Notification


class SimpleUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField(source='full_name', allow_null=True)
    profile_image = serializers.ImageField(allow_null=True)


class SimpleVideoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    slug = serializers.SlugField()
    thumbnail = serializers.ImageField(allow_null=True)


class NotificationSerializer(serializers.ModelSerializer):
    actor_detail = serializers.SerializerMethodField()
    video_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'actor', 'actor_detail', 'video', 'video_detail', 'created_at', 'updated_at']
        read_only_fields = ['id', 'notification_type', 'title', 'message', 'actor', 'video', 'created_at', 'updated_at']

    def get_actor_detail(self, obj):
        if obj.actor:
            return {
                'id': obj.actor.id,
                'username': obj.actor.full_name,
                'full_name': obj.actor.full_name,
                'profile_image': obj.actor.profile_image.url if obj.actor.profile_image else None,
            }
        return None

    def get_video_detail(self, obj):
        if obj.video:
            return {
                'id': obj.video.id,
                'title': obj.video.title,
                'slug': obj.video.slug,
                'thumbnail': obj.video.thumbnail.url if obj.video.thumbnail else None,
            }
        return None

