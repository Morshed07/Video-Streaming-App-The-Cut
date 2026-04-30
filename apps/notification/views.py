from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """Only return notifications for the current user"""
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get only unread notifications"""
        unread_notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, id=None):
        """Mark a specific notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'message': f'{updated_count} notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get the count of unread notifications"""
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': unread_count})

    @action(detail=True, methods=['delete'])
    def delete_notification(self, request, id=None):
        notification = self.get_object()
        notification.delete()
        return Response({'message': 'Notification deleted'})