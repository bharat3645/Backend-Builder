"""
Django URL Configuration for Backend Builder
Generated URLs based on DSL specification
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .views import PostViewSet
from .views import CommentViewSet
from .views import TagViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'tags', TagViewSet)

# API URLs
urlpatterns = [
    path('/api/v1/', include(router.urls)),
    path('/api/v1/auth/', include('rest_framework.urls')),
]

# Custom endpoint patterns
