from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Pages principales
    path('', views.chat_home, name='chat_home'),
    path('conversation/<int:room_id>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('search/', views.search_users, name='search_users'),
    
    # API AJAX
    path('send/<int:room_id>/', views.send_message, name='send_message'),
    path('get-messages/<int:room_id>/', views.get_new_messages, name='get_new_messages'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
    path('update-status/', views.update_status, name='update_status'),
]
