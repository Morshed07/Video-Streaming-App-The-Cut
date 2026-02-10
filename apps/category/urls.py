from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryRetrieveUpdateDestroyView
)

urlpatterns = [
    path('category-list/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('category/<uuid:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
]