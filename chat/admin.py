from django.contrib import admin
from .models import ChatRoom, Message, MessageAttachment, UserStatus


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'participant1', 'participant2', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participant1__username', 'participant2__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'chat_room', 'content_preview', 'created_at', 'is_read', 'is_deleted']
    list_filter = ['is_read', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__username']
    readonly_fields = ['created_at', 'updated_at', 'read_at', 'deleted_at']
    date_hierarchy = 'created_at'
    inlines = [MessageAttachmentInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'file_name', 'file_type', 'get_file_size_display', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_name', 'message__content']
    readonly_fields = ['uploaded_at']
    date_hierarchy = 'uploaded_at'


@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'last_activity', 'is_online', 'custom_message']
    list_filter = ['status', 'last_activity']
    search_fields = ['user__username', 'custom_message']
    readonly_fields = ['last_activity']
    date_hierarchy = 'last_activity'
