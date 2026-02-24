from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VideoViewSet,
    VideoUploadView,
)

app_name = 'videos'

router = DefaultRouter()

router.register(r'video-list', VideoViewSet, basename='video-list'),
router.register(r'video-detail', VideoViewSet, basename='video-detail'),

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', VideoUploadView.as_view(), name='video-upload')
]