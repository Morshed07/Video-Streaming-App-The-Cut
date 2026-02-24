from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AwardViewSet,
    AwardVoteViewSet,
    MonthlyAwardDashboardView
)


router = DefaultRouter()


router.register(r'award-list', AwardViewSet, basename='award'),
router.register(r'award-votes', AwardVoteViewSet, basename='award-vote'),


urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', MonthlyAwardDashboardView.as_view(), name='monthly-awards-dashboard'),

]
