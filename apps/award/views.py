from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Count
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

# Create your views here.


class AwardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for awards
    """
    queryset = Award.objects.filter(is_active=True)
    serializer_class = AwardSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    @action(detail=True, methods=['get'])
    def videos(self, request, slug=None):
        """Get all videos that won this award"""
        award = self.get_object()
        video_awards = VideoAward.objects.filter(award=award).select_related('video')
        videos = [va.video for va in video_awards]
        serializer = VideoListSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, slug=None):
        """Get vote leaderboard for this award"""
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
    """
    ViewSet for award votes
    """
    serializer_class = AwardVoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AwardVote.objects.filter(user=self.request.user).select_related('video', 'award')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def vote(self, request):
        """Vote for a video for an award"""
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