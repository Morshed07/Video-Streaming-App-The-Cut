from django.db import models
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django.db.models import F, Sum
from django.utils import timezone
from datetime import timedelta
from apps.review.models import Review
from apps.award.models import AwardVote
from .models import Video, Favorite, WatchHistory
from .serializers import (
    VideoListSerializer,
    VideoDetailSerializer,
    WatchHistorySerializer,
    VideoUploadSerializer,
)
from apps.review.serializers import ReviewSerializer


# Create your views here.


class VideoPagination(PageNumberPagination):
    page_size = 10 # Default number of items per page
    page_size_query_param = 'page_size' # Allows frontend to request more items per page (?page_size=20)
    max_page_size = 50


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.filter(is_published=True).select_related('category').prefetch_related('tags', 'awards', 'awards__award')
    permission_classes = [IsAuthenticated]
    # pagination_class = StandardResultsSetPagination
    pagination_class = VideoPagination
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'age_rating', 'is_featured', 'is_trending']
    search_fields = ['title', 'description', 'tags__name']
    ordering_fields = ['published_at', 'view_count', 'created_at', 'title']
    ordering = ['-published_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VideoDetailSerializer
        elif self.action == 'upload':
            return VideoUploadSerializer
        return VideoListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply children mode filter
        # if self._is_children_mode_active():
        #     queryset = self._filter_for_children_mode(queryset)
        
        # Filter by tags
        tags = self.request.query_params.get('tags', None)
        if tags:
            tag_list = tags.split(',')
            queryset = queryset.filter(tags__slug__in=tag_list).distinct()
        
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        Video.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        # Ensure request is passed in serializer context
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)

    # --- CUSTOM ACTIONS WITH PAGINATION ---

    @action(detail=False, methods=['get'])
    def featured(self, request):
        videos = self.get_queryset().filter(is_featured=True)
        
        # Manual pagination for custom action
        page = self.paginate_queryset(videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        videos = self.get_queryset().filter(is_trending=True)
        
        # Manual pagination for custom action
        page = self.paginate_queryset(videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def continue_watching(self, request):
        if not request.user.is_authenticated:
            return Response({"success": False, "data": []}, status=status.HTTP_200_OK)
        
        watch_history = WatchHistory.objects.filter(
            user=request.user,
            completed=False,
            last_watched_position__gt=timedelta(seconds=0)
        ).select_related('video').order_by('-last_watched_at')
        
        # Extract videos
        videos_queryset = Video.objects.filter(id__in=watch_history.values_list('video_id', flat=True))
        
        # Paginate
        page = self.paginate_queryset(videos_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(videos_queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, slug=None):
        video = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, video=video)
        
        if not created:
            favorite.delete()
            Video.objects.filter(pk=video.pk).update(like_count=F('like_count') - 1)
            return Response({'favorited': False, 'message': 'Removed from favorites'})
        else:
            Video.objects.filter(pk=video.pk).update(like_count=F('like_count') + 1)
            return Response({'favorited': True, 'message': 'Added to favorites'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_progress(self, request, slug=None):
        video = self.get_object()
        last_position = request.data.get('last_watched_position')
        completed = request.data.get('completed', False)
        
        if not last_position:
            return Response(
                {'error': 'last_watched_position is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse duration string (HH:MM:SS or MM:SS)
        try:
            parts = last_position.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
            else:
                hours = 0
                minutes, seconds = map(int, parts)
            
            position = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, AttributeError):
            return Response(
                {'error': 'Invalid time format. Use HH:MM:SS or MM:SS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        history, created = WatchHistory.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={
                'last_watched_position': position,
                'completed': completed
            }
        )
        
        serializer = WatchHistorySerializer(history, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        video = self.get_object()
        reviews = Review.objects.filter(
            video=video,
            is_approved=True
        ).order_by('-created_at')
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_review(self, request, slug=None):
        video = self.get_object()
        
        # Check if user already reviewed
        if Review.objects.filter(user=request.user, video=video).exists():
            return Response(
                {'error': 'You have already reviewed this video'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user, video=video)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @action(detail=True, methods=['get'])
    # def stats(self, request, slug=None):
    #     video = self.get_object()
        
    #     stats = {
    #         'total_views': video.view_count,
    #         'total_favorites': video.like_count,
    #         'average_rating': video.average_rating or 0,
    #         'total_reviews': video.reviews.filter(is_approved=True).count()
    #     }
        
    #     serializer = VideoStatsSerializer(stats)
    #     return Response(serializer.data)

    # def _is_children_mode_active(self):
    #     """Check if user is in children mode"""
    #     if self.request.user.is_authenticated:
    #         try:
    #             return self.request.user.children_mode.is_currently_active
    #         except ChildrenMode.DoesNotExist:
    #             pass
    #     return False

    # def _filter_for_children_mode(self, queryset):
    #     """Filter videos for children mode"""
    #     try:
    #         parental_control = self.request.user.parental_control
    #         # Filter by age rating
    #         age_ratings = ['G', 'PG']
    #         if parental_control.max_age_rating == 'PG13':
    #             age_ratings.append('PG13')
            
    #         queryset = queryset.filter(
    #             age_rating__in=age_ratings,
    #             is_kids_friendly=True
    #         ).exclude(
    #             category__in=parental_control.blocked_categories.all()
    #         )
    #     except ParentalControl.DoesNotExist:
    #         queryset = queryset.filter(is_kids_friendly=True, age_rating='G')
        
    #     return queryset


class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = VideoUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            video = serializer.save()
            return Response(VideoDetailSerializer(video, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrendingVideosListView(APIView):
    # Attach the pagination class
    pagination_class = VideoPagination

    def get(self, request, format=None):
        # 1. Get the full queryset
        trending_videos = Video.objects.filter(is_trending=True).order_by('-published_at')
        
        # 2. Instantiate the paginator
        paginator = self.pagination_class()
        
        # 3. Paginate the queryset based on the request URL parameters
        paginated_videos = paginator.paginate_queryset(trending_videos, request, view=self)
        
        # 4. Serialize ONLY the paginated videos (make sure you pass paginated_videos here!)
        serializer = VideoListSerializer(paginated_videos, many=True, context={'request': request})
        
        # 5. Return the structured response
        return Response(
            {
                "success": True,
                "pagination": {
                    "count": paginator.page.paginator.count,
                    "total_pages": paginator.page.paginator.num_pages,
                    "current_page": paginator.page.number,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link()
                },
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
    

class TopVotedVideosListView(APIView):
    # Attach the pagination class
    pagination_class = VideoPagination

    def get(self, request, format=None):
        # Note: We removed the [:20] slicing at the end so the paginator can handle limits
        top_videos = Video.objects.annotate(
            total_votes=Count('award_votes')
        ).filter(
            total_votes__gt=0
        ).order_by('-total_votes')

        # 2. Instantiate the paginator
        paginator = self.pagination_class()

        # 3. Paginate the queryset based on the request (e.g., ?page=2)
        paginated_videos = paginator.paginate_queryset(top_videos, request, view=self)

        # 4. Serialize ONLY the paginated items
        serializer = VideoListSerializer(
            paginated_videos, 
            many=True, 
            context={'request': request}
        )

        # 5. Return your custom response with pagination metadata included
        return Response(
            {
                "success": True,
                "pagination": {
                    "count": paginator.page.paginator.count,         # Total number of videos
                    "total_pages": paginator.page.paginator.num_pages, # Total number of pages
                    "current_page": paginator.page.number,             # Current page number
                    "next": paginator.get_next_link(),                 # URL for the next page
                    "previous": paginator.get_previous_link()          # URL for the previous page
                },
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )