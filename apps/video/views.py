from django.db import models
from django.db.models import Count, Q
from django.db.utils import IntegrityError
from rest_framework.views import APIView
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
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
import hmac, hashlib
from .mediaconvert import trigger_hls_transcode


# Create your views here.


class VideoPagination(PageNumberPagination):
    page_size = 10 # Default number of items per page
    page_size_query_param = 'page_size' # Allows frontend to request more items per page (?page_size=20)
    max_page_size = 50


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.filter(is_published=True).select_related(
        'category'
    ).prefetch_related(
        'tags', 'awards', 'awards__award'
    ).order_by('-updated_at')
    
    permission_classes = [IsAuthenticated]
    pagination_class = VideoPagination
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'age_rating', 'is_featured', 'is_trending']
    search_fields = ['title', 'description', 'tags__name']
    ordering_fields = ['published_at', 'view_count', 'created_at', 'title']
    ordering = ['-updated_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VideoDetailSerializer
        elif self.action == 'upload':
            return VideoUploadSerializer
        return VideoListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 1. APPLY KID MODE FILTER
        # If user.kid_mode is True, only show videos marked as kids_friendly
        if hasattr(user, 'kid_mode') and user.kid_mode:
            queryset = queryset.filter(is_kids_friendly=True, is_published=True)
        
        # 2. FILTER BY TAGS (Existing logic)
        tags = self.request.query_params.get('tags', None)
        if tags:
            tag_list = tags.split(',')
            queryset = queryset.filter(tags__slug__in=tag_list).distinct()
        
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 1. Atomic update for view count (Efficient)
        Video.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        
        if request.user.is_authenticated:
            WatchHistory.objects.get_or_create(user=request.user, video=instance)
        
        # 3. Explicitly pass context to ensure absolute URLs (thumbnail, video_file)
        serializer = self.get_serializer(instance, context={'request': request})
        
        return Response(serializer.data)

    # --- HELPER FOR PAGINATED ACTIONS ---
    def _get_paginated_action_response(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # --- CUSTOM ACTIONS ---

    @action(detail=False, methods=['get'])
    def featured(self, request):
        # uses get_queryset() so Kid Mode filter is automatically applied
        videos = self.get_queryset().filter(is_featured=True)
        return self._get_paginated_action_response(videos)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        videos = self.get_queryset().filter(is_trending=True)
        return self._get_paginated_action_response(videos)

    @action(detail=False, methods=['get'])
    def continue_watching(self, request):
        watch_history = WatchHistory.objects.filter(
            user=request.user,
            completed=False,
            last_watched_position__gt=timedelta(seconds=0)
        ).select_related('video').order_by('-last_watched_at')
        
        # Get video IDs from history
        video_ids = watch_history.values_list('video_id', flat=True)
        # Query videos using the main queryset logic to maintain Kid Mode safety
        videos = self.get_queryset().filter(id__in=video_ids)
        
        return self._get_paginated_action_response(videos)

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, slug=None):
        video = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, video=video)
        
        if not created:
            favorite.delete()
            Video.objects.filter(pk=video.pk).update(like_count=F('like_count') - 1)
            return Response({'favorited': False, 'message': 'Removed from favorites'})
        
        Video.objects.filter(pk=video.pk).update(like_count=F('like_count') + 1)
        return Response({'favorited': True, 'message': 'Added to favorites'})

    @action(detail=True, methods=['post'])
    def update_progress(self, request, slug=None):
        video = self.get_object()
        last_position = request.data.get('last_watched_position')
        completed = request.data.get('completed', False)
        
        if not last_position:
            return Response({'error': 'last_watched_position is required'}, status=400)
        
        try:
            parts = last_position.split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
                position = timedelta(hours=h, minutes=m, seconds=s)
            else:
                m, s = map(int, parts)
                position = timedelta(minutes=m, seconds=s)
        except:
            return Response({'error': 'Use HH:MM:SS or MM:SS'}, status=400)
        
        history, _ = WatchHistory.objects.update_or_create(
            user=request.user, video=video,
            defaults={'last_watched_position': position, 'completed': completed}
        )
        return Response(WatchHistorySerializer(history, context={'request': request}).data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        video = self.get_object()
        reviews = Review.objects.filter(video=video, is_approved=True).order_by('-created_at')
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        return Response(ReviewSerializer(reviews, many=True, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def add_review(self, request, slug=None):
        video = self.get_object()
        if Review.objects.filter(user=request.user, video=video).exists():
            return Response({'error': 'Already reviewed'}, status=400)
        
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user, video=video)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_published_videos(self, request):
        """List of videos uploaded by the current user that ARE published"""
        videos = Video.objects.filter(
            upload_by=request.user, 
            is_published=True
        ).order_by('-published_at')
        return self._get_paginated_action_response(videos)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_pending_videos(self, request):
        """List of videos uploaded by the current user that are NOT yet published"""
        # Note: We use Video.objects here instead of get_queryset() 
        # because get_queryset() excludes unpublished videos by default.
        videos = Video.objects.filter(
            upload_by=request.user,
            is_published=False
        ).order_by('-created_at')
        return self._get_paginated_action_response(videos)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_favorites(self, request):
        """List of videos the current user has favorited"""
        # We find all favorites for this user and get the related video objects
        favorite_ids = Favorite.objects.filter(user=request.user).values_list('video_id', flat=True)
        
        # We use get_queryset() here to ensure Kid Mode filters still apply to favorites
        videos = self.get_queryset().filter(id__in=favorite_ids)
        return self._get_paginated_action_response(videos)


class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = VideoUploadSerializer(
            data=request.data, 
            context={'request': request}
        )
        if serializer.is_valid():
            try:
                video = serializer.save()

                # ── Trigger HLS transcoding after upload ──
                try:
                    # video.video_file.name = the S3 key
                    job_id, hls_url = trigger_hls_transcode(
                        video_id=video.id,
                        s3_input_key=video.video_file.name
                    )
                    # Save HLS info to model
                    video.hls_job_id = job_id
                    video.hls_url = hls_url
                    video.hls_status = 'processing'
                    video.save(update_fields=['hls_job_id', 'hls_url', 'hls_status'])

                except Exception as e:
                    # Don't fail the upload if transcode trigger fails
                    print(f"MediaConvert trigger failed: {e}")

                return Response(
                    VideoDetailSerializer(video, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
            except IntegrityError:
                return Response(
                    {"error": "A video with a similar title already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrendingVideosListView(APIView):
    # Attach the pagination class
    pagination_class = VideoPagination

    def get(self, request, format=None):
        # 1. Get the full queryset
        trending_videos = Video.objects.filter(is_trending=True).order_by('-updated_at')
        
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


class ChildrenFriendlyVideosListView(APIView):
    pagination_class = VideoPagination
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        print(f"User: {user.email} | Kid Mode: {user.kid_mode}")
        # If Kid Mode is ON, restrict to kids-friendly only
        if user.kid_mode:
            videos = Video.objects.filter(is_published=True, is_kids_friendly=True).order_by('-updated_at')
        else:
            # If Kid Mode is OFF, show everything published
            videos = Video.objects.filter(is_published=True).order_by('-updated_at')

        # Use the paginator helper we built earlier to keep the code clean
        paginator = self.pagination_class()
        paginated_videos = paginator.paginate_queryset(videos, request, view=self)
        
        serializer = VideoListSerializer(paginated_videos, many=True, context={'request': request})
        
        # Use the custom response method from your VideoPagination class
        return paginator.get_paginated_response(serializer.data)
    

class HistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        history = WatchHistory.objects.filter(user=request.user).select_related('video').order_by('-last_watched_at')
        serializer = WatchHistorySerializer(history, many=True, context={'request': request})
        return Response(serializer.data)
    

class MediaConvertWebhookView(APIView):
    permission_classes = [AllowAny]  # AWS calls this, no auth token

    def post(self, request, format=None):
        body = request.data

        # AWS SNS first sends a subscription confirmation
        if body.get('Type') == 'SubscriptionConfirmation':
            import urllib.request
            urllib.request.urlopen(body['SubscribeURL'])
            return Response({'status': 'subscribed'})

        # Parse the actual MediaConvert event
        message = json.loads(body.get('Message', '{}'))
        detail = message.get('detail', {})
        job_id = detail.get('jobId')
        job_status = detail.get('status')  # COMPLETE or ERROR

        if not job_id:
            return Response({'status': 'ignored'})

        try:
            video = Video.objects.get(hls_job_id=job_id)
            if job_status == 'COMPLETE':
                video.hls_status = 'ready'
            elif job_status == 'ERROR':
                video.hls_status = 'failed'
            video.save(update_fields=['hls_status'])
        except Video.DoesNotExist:
            pass

        return Response({'status': 'ok'})