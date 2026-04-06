from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import (
    ReviewSerializer
)
from .models import Review

# Create your views here.


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        video_id = request.data.get('video')
        
        # Check if review already exists
        try:
            review = Review.objects.get(user=user, video_id=video_id)
            # Update existing review
            serializer = ReviewSerializer(review, data=request.data, context={'request': request}, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            review = serializer.save()
            return Response(ReviewSerializer(review, context={'request': request}).data, status=status.HTTP_200_OK)
        except Review.DoesNotExist:
            # Create new review
            serializer = ReviewSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            review = serializer.save()
            return Response(ReviewSerializer(review, context={'request': request}).data, status=status.HTTP_201_CREATED)