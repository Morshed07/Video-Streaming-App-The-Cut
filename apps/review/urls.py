from django.urls import path
from .views import ReviewCreateView


urlpatterns = [
    path('review/create/', ReviewCreateView.as_view(), name='review-create'),

]