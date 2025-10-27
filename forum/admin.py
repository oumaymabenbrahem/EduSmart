from django.contrib import admin
from .models import Category, Topic, Post, Comment, Report


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active', 'get_topics_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    def get_topics_count(self, obj):
        return obj.topics.filter(is_active=True).count()
    get_topics_count.short_description = 'Sujets'


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'status', 'posts_count', 'views', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'category', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def posts_count(self, obj):
        return obj.posts_count
    posts_count.short_description = 'Réponses'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'is_solution', 'is_active', 'likes_count', 'created_at']
    list_filter = ['is_active', 'is_solution', 'created_at']
    search_fields = ['content', 'author__username', 'topic__title']
    raw_id_fields = ['author', 'topic']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def likes_count(self, obj):
        return obj.likes_count
    likes_count.short_description = 'Likes'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['author', 'post']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'content_id', 'reporter', 'reason', 'status', 'created_at']
    list_filter = ['content_type', 'reason', 'status', 'created_at']
    search_fields = ['description', 'reporter__username']
    raw_id_fields = ['reporter', 'reviewed_by']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    actions = ['mark_as_reviewed', 'mark_as_resolved']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed', reviewed_by=request.user)
    mark_as_reviewed.short_description = "Marquer comme examiné"
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', reviewed_by=request.user, resolved_at=timezone.now())
    mark_as_resolved.short_description = "Marquer comme résolu"
