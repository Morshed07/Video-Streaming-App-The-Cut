from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    Award,
    VideoAward,
    AwardVote
)
from .serializers import (
    AwardSerializer,
    AwardVoteSerializer
)
from apps.video.models import Video
from apps.video.serializers import VideoListSerializer
from rest_framework.views import APIView

# Create your views here.


class AwardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Award.objects.filter(is_active=True)
    serializer_class = AwardSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    @action(detail=True, methods=['get'])
    def videos(self, request, slug=None):
        award = self.get_object()
        video_awards = VideoAward.objects.filter(award=award).select_related('video')
        videos = [va.video for va in video_awards]
        serializer = VideoListSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, slug=None):
        award = self.get_object()
        
        # Get vote counts per video
        votes = AwardVote.objects.filter(award=award).values('video').annotate(
            vote_count=Count('id')
        ).order_by('-vote_count')[:20]
        
        # Get video details
        video_ids = [v['video'] for v in votes]
        videos = Video.objects.filter(id__in=video_ids, is_published=True)
        video_dict = {v.id: v for v in videos}
        
        leaderboard = []
        for vote_data in votes:
            video = video_dict.get(vote_data['video'])
            if video:
                leaderboard.append({
                    'rank': len(leaderboard) + 1,
                    'video': VideoListSerializer(video, context={'request': request}).data,
                    'votes': vote_data['vote_count']
                })
        
        return Response(leaderboard)


class AwardVoteViewSet(viewsets.ModelViewSet):
    serializer_class = AwardVoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AwardVote.objects.filter(user=self.request.user).select_related('video', 'award')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def vote(self, request):
        video_id = request.data.get('video_id')
        award_id = request.data.get('award_id')
        
        if not video_id or not award_id:
            return Response(
                {'error': 'video_id and award_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            video = Video.objects.get(id=video_id, is_published=True)
            award = Award.objects.get(id=award_id, is_active=True)
        except (Video.DoesNotExist, Award.DoesNotExist):
            return Response(
                {'error': 'Video or Award not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remove existing vote if re-voting
        AwardVote.objects.filter(
            user=request.user,
            video=video,
            award=award
        ).delete()
        
        # Create new vote
        vote = AwardVote.objects.create(
            user=request.user,
            video=video,
            award=award
        )
        
        serializer = self.get_serializer(vote)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class MonthlyAwardDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        year = now.year
        month = now.month

        # -------- CURRENT MONTH TOP 3 --------
        current_votes = (
            AwardVote.objects.filter(
                video__upload_by=request.user,
                voted_at__year=year,
                voted_at__month=month
            )
        )

        total_votes_this_month = current_votes.count()

        top_videos_data = (
            current_votes
            .values('video')
            .annotate(total_votes=Count('id'))
            .order_by('-total_votes')[:3]
        )

        top_video_ids = [item['video'] for item in top_videos_data]

        videos = (
            Video.objects
            .filter(id__in=top_video_ids)
            .annotate(
                total_votes=Count(
                    'award_votes',
                    filter=Q(
                        award_votes__voted_at__year=year,
                        award_votes__voted_at__month=month
                    )
                )
            )
            .order_by('-total_votes')
        )

        top_videos = []
        for index, video in enumerate(videos, start=1):
            thumbnail_url = None
            if video.thumbnail:
                thumbnail_url = request.build_absolute_uri(video.thumbnail.url)

            top_videos.append({
                "id": video.id,
                "title": video.title,
                "thumbnail": thumbnail_url,
                "total_votes": video.total_votes,
                "rank": index
            })

        # -------- USER STATS --------
        my_votes_this_month = 0
        if request.user.is_authenticated:
            my_votes_this_month = AwardVote.objects.filter(
                user=request.user,
                voted_at__year=year,
                voted_at__month=month
            ).count()

        # -------- PREVIOUS MONTH TOP VIDEO --------
        prev_month = month - 1 or 12
        prev_year = year if month != 1 else year - 1

        previous_votes = (
            AwardVote.objects
            .filter(voted_at__year=prev_year, voted_at__month=prev_month)
            .values('video')
            .annotate(total_votes=Count('id'))
            .order_by('-total_votes')
            .first()
        )

        previous_top_video = None
        if previous_votes:
            video = Video.objects.get(id=previous_votes['video'])
            previous_top_video = {
                "id": video.id,
                "title": video.title,
                "thumbnail": video.thumbnail.url if video.thumbnail else None,
                "total_votes": previous_votes['total_votes']
            }

        return Response({
            "current_month": {
                "year": year,
                "month": month,
                "total_votes": total_votes_this_month,
                "my_votes_this_month": my_votes_this_month,
                "top_videos": top_videos
            },
            "previous_month_top_video": previous_top_video
        })
