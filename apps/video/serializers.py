from urllib import request

from rest_framework import serializers
from .models import Video

from apps.award.models import AwardVote, Award

from apps.category.serializers import (
    CategorySerializer,
    TagSerializer
)
from apps.video.models import (
    Favorite,
    WatchHistory,
)
from apps.review.models import Review
from apps.review.serializers import ReviewSerializer


class VideoListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id',
            'title', 
            'slug', 
            'thumbnail',
            'video_file',
            'hls_url',        # ← add this
            'hls_status',
            'duration',  
            'status',
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
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    awards = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()
    user_review = serializers.SerializerMethodField()
    user_voted_awards = serializers.SerializerMethodField()
    related_videos = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description',
            'video_file', 'hls_url', 'hls_status', 'thumbnail', 'duration',
            'age_rating', 'category', 'status',
            'awards', 'tags', 'view_count', 'like_count', 'average_rating',
            'is_favorited', 'watch_progress', 'user_review', 'user_voted_awards',
            'reviews', 'is_featured', 'is_trending', 'is_kids_friendly', 'related_videos',
            'published_at', 'created_at', 'updated_at'
        ]

    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')[:5]
        return ReviewSerializer(reviews, many=True, context=self.context).data
    
    def get_awards(self, obj): 
        # Get all active awards
        all_awards = Award.objects.filter(is_active=True).order_by('order')
        
        awards_data = []
        request = self.context.get('request')
        current_user = None
        
        # Get current user - handle both authenticated and anonymous users
        if request:
            current_user = getattr(request, 'user', None)
        
        for award in all_awards:
            # Count votes for this award on this video
            vote_count = AwardVote.objects.filter(video=obj, award=award).count()
            
            # Check if user voted for this award on this video
            user_voted = False
            if current_user and current_user.is_authenticated:
                user_voted = AwardVote.objects.filter(
                    user=current_user,
                    video=obj,
                    award=award
                ).exists()

            awards_data.append({
                'award_id': award.id,
                'award_order': award.order,
                'award_title': award.title,
                'award_description': award.description,
                'vote_count': vote_count,
                'user_voted': user_voted
            })

        return awards_data

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

        request = self.context.get('request')
        
        if request and request.user.is_authenticated:
            return list(AwardVote.objects.filter(
                user=request.user, 
                video=obj
            ).values_list('award_id', 'award__title', flat=False))
        return []
    
    def get_related_videos(self, obj):
        # Get videos that share at least one tag with the current video
        related_videos = Video.objects.filter(category=obj.category).exclude(id=obj.id).distinct().order_by('-published_at')[:10]
        
        # Get the actual Django request object from the parent serializer's context
        current_request = self.context.get('request')
        
        # Pass the correct request into the nested serializer
        return VideoListSerializer(
            related_videos, 
            many=True, 
            context={'request': current_request}
        ).data
    

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
    total_views = serializers.IntegerField()
    total_favorites = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    watch_time_minutes = serializers.IntegerField()


class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description',
            'video_file', 'thumbnail', 'duration', 'age_rating',
            'category', 'tags', 'is_published', 'is_featured',
            'is_kids_friendly', 'published_at', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def create(self, validated_data):
        validated_data['upload_by'] = self.context['request'].user
        return super().create(validated_data)
