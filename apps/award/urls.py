from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AwardViewSet,
    AwardVoteViewSet
)


router = DefaultRouter()


router.register(r'award-list', AwardViewSet, basename='award'),
router.register(r'award-votes', AwardVoteViewSet, basename='award-vote'),


urlpatterns = [
    path('', include(router.urls)),

]
