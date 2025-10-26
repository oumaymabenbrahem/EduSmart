from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q, Max, Count, Case, When, IntegerField
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from .models import ChatRoom, Message, MessageAttachment, UserStatus
import json

User = get_user_model()


@login_required
def chat_home(request):
    """
    Page d'accueil du chat - Liste des conversations
    """
    # Récupérer toutes les conversations de l'utilisateur
    chat_rooms = ChatRoom.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).select_related('participant1', 'participant2').annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
    # Enrichir avec les infos du dernier message
    rooms_data = []
    for room in chat_rooms:
        other_user = room.get_other_participant(request.user)
        last_message = room.get_last_message()
        unread_count = room.messages.filter(
            ~Q(sender=request.user),
            is_read=False
        ).count()
        
        rooms_data.append({
            'room': room,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    # Mettre à jour le statut de l'utilisateur
    user_status, created = UserStatus.objects.get_or_create(user=request.user)
    user_status.update_activity()
    
    context = {
        'rooms_data': rooms_data,
        'active_page': 'chat',
    }
    return render(request, 'chat/chat_home.html', context)


@login_required
def conversation_detail(request, room_id):
    """
    Affiche les détails d'une conversation
    """
    chat_room = get_object_or_404(
        ChatRoom,
        id=room_id
    )
    
    # Vérifier que l'utilisateur fait partie de la conversation
    if request.user not in [chat_room.participant1, chat_room.participant2]:
        return redirect('chat:chat_home')
    
    other_user = chat_room.get_other_participant(request.user)
    
    # Récupérer les messages
    messages = chat_room.messages.filter(
        is_deleted=False
    ).select_related('sender').prefetch_related('attachments').order_by('created_at')
    
    # Marquer tous les messages reçus comme lus
    unread_messages = messages.filter(
        ~Q(sender=request.user),
        is_read=False
    )
    for message in unread_messages:
        message.mark_as_read()
    
    # Mettre à jour le statut de l'utilisateur
    user_status, created = UserStatus.objects.get_or_create(user=request.user)
    user_status.update_activity()
    
    # Récupérer le statut de l'autre utilisateur
    other_user_status, created = UserStatus.objects.get_or_create(user=other_user)
    
    context = {
        'chat_room': chat_room,
        'other_user': other_user,
        'other_user_status': other_user_status,
        'messages': messages,
        'active_page': 'chat',
    }
    return render(request, 'chat/conversation_detail.html', context)


@login_required
@require_POST
def send_message(request, room_id):
    """
    Envoie un message dans une conversation (API AJAX)
    """
    chat_room = get_object_or_404(ChatRoom, id=room_id)
    
    # Vérifier que l'utilisateur fait partie de la conversation
    if request.user not in [chat_room.participant1, chat_room.participant2]:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Le message ne peut pas être vide'}, status=400)
        
        # Créer le message
        message = Message.objects.create(
            chat_room=chat_room,
            sender=request.user,
            content=content
        )
        
        # Mettre à jour le timestamp de la conversation
        chat_room.updated_at = timezone.now()
        chat_room.save(update_fields=['updated_at'])
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read,
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Format JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_new_messages(request, room_id):
    """
    Récupère les nouveaux messages depuis un certain timestamp (API AJAX pour polling)
    """
    chat_room = get_object_or_404(ChatRoom, id=room_id)
    
    # Vérifier que l'utilisateur fait partie de la conversation
    if request.user not in [chat_room.participant1, chat_room.participant2]:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    last_message_id = request.GET.get('last_message_id', 0)
    
    # Récupérer les nouveaux messages
    new_messages = chat_room.messages.filter(
        id__gt=last_message_id,
        is_deleted=False
    ).select_related('sender').order_by('created_at')
    
    # Marquer les messages reçus comme lus
    for message in new_messages:
        if message.sender != request.user and not message.is_read:
            message.mark_as_read()
    
    messages_data = [
        {
            'id': msg.id,
            'content': msg.content,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'created_at': msg.created_at.isoformat(),
            'is_read': msg.is_read,
        }
        for msg in new_messages
    ]
    
    # Récupérer le statut de l'autre utilisateur
    other_user = chat_room.get_other_participant(request.user)
    other_user_status, created = UserStatus.objects.get_or_create(user=other_user)
    
    return JsonResponse({
        'messages': messages_data,
        'other_user_online': other_user_status.is_online(),
        'other_user_status': other_user_status.status,
    })


@login_required
def start_conversation(request, user_id):
    """
    Démarre une nouvelle conversation avec un utilisateur
    """
    other_user = get_object_or_404(User, id=user_id)
    
    # Ne pas permettre de créer une conversation avec soi-même
    if other_user == request.user:
        return redirect('chat:chat_home')
    
    # Créer ou récupérer la conversation
    chat_room, created = ChatRoom.get_or_create_room(request.user, other_user)
    
    return redirect('chat:conversation_detail', room_id=chat_room.id)


@login_required
def search_users(request):
    """
    Recherche d'utilisateurs pour démarrer une conversation
    """
    query = request.GET.get('q', '').strip()
    
    if query:
        # Rechercher les utilisateurs (exclure l'utilisateur actuel)
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:20]
    else:
        # Afficher tous les utilisateurs sauf l'utilisateur actuel
        users = User.objects.exclude(id=request.user.id)[:20]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Réponse AJAX
        users_data = [
            {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
                'is_staff': user.is_staff,
            }
            for user in users
        ]
        return JsonResponse({'users': users_data})
    
    context = {
        'users': users,
        'query': query,
        'active_page': 'chat',
    }
    return render(request, 'chat/search_users.html', context)


@login_required
@require_POST
def delete_message(request, message_id):
    """
    Supprime un message (soft delete)
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Vérifier que l'utilisateur est l'expéditeur
    if message.sender != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    message.soft_delete()
    
    return JsonResponse({'success': True})


@login_required
def get_unread_count(request):
    """
    Retourne le nombre total de messages non lus (pour le badge de notification)
    """
    unread_count = Message.objects.filter(
        chat_room__in=ChatRoom.objects.filter(
            Q(participant1=request.user) | Q(participant2=request.user)
        ),
        is_read=False
    ).exclude(sender=request.user).count()
    
    return JsonResponse({'unread_count': unread_count})


@login_required
@require_POST
def update_status(request):
    """
    Met à jour le statut de l'utilisateur
    """
    try:
        data = json.loads(request.body)
        new_status = data.get('status', 'online')
        custom_message = data.get('custom_message', '')
        
        user_status, created = UserStatus.objects.get_or_create(user=request.user)
        user_status.status = new_status
        user_status.custom_message = custom_message
        user_status.update_activity()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
