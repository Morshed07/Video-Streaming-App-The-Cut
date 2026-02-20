from rest_framework import serializers
from .models import (
    Award,
    VideoAward,
    AwardVote
)


class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = ['id', 'title', 'slug', 'description', 'order', 'is_active']
    

class VideoAwardSerializer(serializers.ModelSerializer):
    award = AwardSerializer(read_only=True)
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = VideoAward
        fields = ['id', 'award', 'rank', 'awarded_date', 'vote_count']

    def get_vote_count(self, obj):
        return AwardVote.objects.filter(video=obj.video, award=obj.award).count()


class AwardVoteSerializer(serializers.ModelSerializer):
    award_name = serializers.CharField(source='award.name', read_only=True)

    class Meta:
        model = AwardVote
        fields = ['id', 'video', 'award', 'award_name', 'voted_at']
        read_only_fields = ['voted_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Remove existing vote if re-voting
        AwardVote.objects.filter(
            user=validated_data['user'],
            video=validated_data['video'],
            award=validated_data['award']
        ).delete()
        return super().create(validated_data)
