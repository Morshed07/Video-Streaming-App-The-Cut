from rest_framework import serializers

from .models import Review, ReviewHelpful


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    is_helpful = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user_name', 'user_avatar', 'video', 'rating', 
            'review_text', 'helpful_count', 'is_helpful', 'can_edit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user_name', 'user_avatar', 'helpful_count', 'created_at', 'updated_at']

    def get_user_avatar(self, obj):
        # Assuming user model has avatar field
        if hasattr(obj.user, 'avatar') and obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
        return None

    def get_is_helpful(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ReviewHelpful.objects.filter(user=request.user, review=obj).exists()
        return False

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)