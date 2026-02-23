from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VideoViewSet,
)

app_name = 'videos'

router = DefaultRouter()
router.register(r'video-list', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]