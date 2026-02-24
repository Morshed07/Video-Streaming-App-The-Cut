from rest_framework import serializers
from .models import (
    Award,
    AwardVote
)

from apps.video.models import Video


class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = ['id', 'title', 'description', 'order', 'is_active']
    

class AwardWithVoteSerializer(serializers.Serializer):
    award_id = serializers.IntegerField()
    order = serializers.IntegerField()
    award_title = serializers.CharField()
    award_description = serializers.CharField()
    vote_count = serializers.IntegerField()
    user_voted = serializers.BooleanField()


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


class MonthlyTopVideoSerializer(serializers.ModelSerializer):
    total_votes = serializers.IntegerField()
    uploaded_by = serializers.CharField(source='upload_by.full_name', read_only=True)

    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'slug',
            'thumbnail',
            'total_votes',
            'uploaded_by',
            'average_rating'
        ]