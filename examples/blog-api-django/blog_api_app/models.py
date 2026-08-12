"""
Django Model Template for Backend Builder
Generated models based on DSL specification
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    """User model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=255, null=False, blank=False, unique=True)
    password = models.CharField(max_length=255, null=False, blank=False)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    avatar = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        pass

    def __str__(self):
        return f"User {self.pk}"

class Post(models.Model):
    """Post model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, null=False, blank=False)
    slug = models.CharField(max_length=255, null=True, blank=True, unique=True)
    content = models.TextField(null=False, blank=False)
    excerpt = models.TextField(null=True, blank=True)
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    featured_image = models.URLField(null=True, blank=True)
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='post_author_set')
    tags = models.ManyToManyField('Tag', blank=True, related_name='post_tags_set')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    def __str__(self):
        return f"Post {self.pk}"

class Comment(models.Model):
    """Comment model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField(null=False, blank=False)
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='comment_author_set')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comment_post_set')
    parent = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, related_name='comment_parent_set')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    def __str__(self):
        return f"Comment {self.pk}"

class Tag(models.Model):
    """Tag model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False, unique=True)
    slug = models.CharField(max_length=255, null=True, blank=True, unique=True)
    color = models.CharField(max_length=7, null=True, blank=True, default="#3B82F6")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        pass

    def __str__(self):
        return f"Tag {self.pk}"

