from rest_framework import serializers
from .models import Video

from apps.award.models import AwardVote

from apps.award.serializers import (
    VideoAwardSerializer,
    AwardSerializer
)
from apps.category.serializers import CategorySerializer, TagSerializer
from apps.video.models import (
    Favorite,
    WatchHistory,
)
from apps.review.models import Review
from apps.review.serializers import ReviewSerializer


class VideoListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for video lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    duration_display = serializers.CharField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id',
            'title', 
            'slug', 
            'thumbnail',
            'duration', 
            'duration_display', 
            'category_name', 
            'age_rating',
            'view_count', 
            'like_count', 
            'average_rating', 
            'is_favorited',
            'watch_progress', 
            'is_featured', 
            'is_trending', 
            'published_at'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, video=obj).exists()
        return False

    def get_watch_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                history = WatchHistory.objects.get(user=request.user, video=obj)
                return {
                    'percentage': history.progress_percentage,
                    'last_position': str(history.last_watched_position),
                    'completed': history.completed
                }
            except WatchHistory.DoesNotExist:
                pass
        return None


class VideoDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual video view"""
    category = CategorySerializer(read_only=True)
    award = VideoAwardSerializer(source='awards.all', many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    duration_display = serializers.CharField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()
    user_review = serializers.SerializerMethodField()
    user_voted_awards = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description',
            'video_file', 'thumbnail', 'duration',
            'duration_display', 'age_rating', 'category',
            'tags', 'award', 'view_count', 'like_count', 'average_rating',
            'is_favorited', 'watch_progress', 'user_review', 'user_voted_awards',
            'reviews', 'is_featured', 'is_trending', 'is_kids_friendly',
            'published_at', 'created_at'
        ]

    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')[:5]
        return ReviewSerializer(reviews, many=True, context=self.context).data


    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, video=obj).exists()
        return False

    def get_watch_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                history = WatchHistory.objects.get(user=request.user, video=obj)
                return {
                    'percentage': history.progress_percentage,
                    'last_position': str(history.last_watched_position),
                    'completed': history.completed,
                    'last_watched_at': history.last_watched_at
                }
            except WatchHistory.DoesNotExist:
                pass
        return None

    def get_user_review(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                review = Review.objects.get(user=request.user, video=obj)
                return ReviewSerializer(review, context=self.context).data
            except Review.DoesNotExist:
                pass
        return None

    def get_user_voted_awards(self, obj):
        """Get list of award IDs the user has voted for this video"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return list(AwardVote.objects.filter(
                user=request.user, 
                video=obj
            ).values_list('award_id', flat=True))
        return []
    

class WatchHistorySerializer(serializers.ModelSerializer):
    video = VideoListSerializer(read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = WatchHistory
        fields = [
            'id', 'video', 'watch_duration', 'last_watched_position',
            'progress_percentage', 'completed', 'last_watched_at', 'first_watched_at'
        ]
        read_only_fields = ['first_watched_at']


class VideoStatsSerializer(serializers.Serializer):
    """Serializer for video statistics"""
    total_views = serializers.IntegerField()
    total_favorites = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    watch_time_minutes = serializers.IntegerField()