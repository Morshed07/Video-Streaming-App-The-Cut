from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import (
    ReviewSerializer
)

# Create your views here.


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        review = serializer.save()
        return Response(ReviewSerializer(review, context={'request': request}).data, status=status.HTTP_201_CREATED)