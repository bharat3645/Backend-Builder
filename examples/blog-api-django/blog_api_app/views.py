"""
Django REST Framework Views for InfraNest
Generated views based on DSL specification
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import User
from .serializers import UserSerializer
from .models import Post
from .serializers import PostSerializer
from .models import Comment
from .serializers import CommentSerializer
from .models import Tag
from .serializers import TagSerializer

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Permissions
    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ['create']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    # Filtering
    
    # Search
    
    # Ordering
    
    def get_queryset(self):
        """Get queryset based on permissions"""
        queryset = self.queryset
        
        # Apply ownership filtering if needed
        if self.request.user.is_authenticated:
            # Filter by owner if user field exists
            if hasattr(self.queryset.model, 'user'):
                queryset = queryset.filter(user=self.request.user)
            elif hasattr(self.queryset.model, 'author'):
                queryset = queryset.filter(author=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set user when creating objects"""
        # Auto-assign user if model has user/author field
        if hasattr(serializer.Meta.model, 'user') and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        elif hasattr(serializer.Meta.model, 'author') and self.request.user.is_authenticated:
            serializer.save(author=self.request.user)
        else:
            serializer.save()

class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for Post model"""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Permissions
    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ['create']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    # Filtering
    
    # Search
    
    # Ordering
    
    def get_queryset(self):
        """Get queryset based on permissions"""
        queryset = self.queryset
        
        # Apply ownership filtering if needed
        
        return queryset
    
    def perform_create(self, serializer):
        """Set user when creating objects"""
        # Auto-assign user if model has user/author field
        if hasattr(serializer.Meta.model, 'user') and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        elif hasattr(serializer.Meta.model, 'author') and self.request.user.is_authenticated:
            serializer.save(author=self.request.user)
        else:
            serializer.save()

class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Comment model"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Permissions
    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ['create']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    # Filtering
    
    # Search
    
    # Ordering
    
    def get_queryset(self):
        """Get queryset based on permissions"""
        queryset = self.queryset
        
        # Apply ownership filtering if needed
        
        return queryset
    
    def perform_create(self, serializer):
        """Set user when creating objects"""
        # Auto-assign user if model has user/author field
        if hasattr(serializer.Meta.model, 'user') and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        elif hasattr(serializer.Meta.model, 'author') and self.request.user.is_authenticated:
            serializer.save(author=self.request.user)
        else:
            serializer.save()

class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tag model"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Permissions
    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    # Filtering
    
    # Search
    
    # Ordering
    
    def get_queryset(self):
        """Get queryset based on permissions"""
        queryset = self.queryset
        
        # Apply ownership filtering if needed
        
        return queryset
    
    def perform_create(self, serializer):
        """Set user when creating objects"""
        # Auto-assign user if model has user/author field
        serializer.save()

