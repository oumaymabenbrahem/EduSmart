from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, UserStatus

User = get_user_model()


class ChatRoomTestCase(TestCase):
    def setUp(self):
        """Configure les données de test"""
        self.user1 = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123'
        )
    
    def test_create_chat_room(self):
        """Test de création d'une conversation"""
        room, created = ChatRoom.get_or_create_room(self.user1, self.user2)
        self.assertTrue(created)
        self.assertIn(self.user1, [room.participant1, room.participant2])
        self.assertIn(self.user2, [room.participant1, room.participant2])
    
    def test_chat_room_unique(self):
        """Test qu'il n'y a qu'une seule conversation entre deux utilisateurs"""
        room1, created1 = ChatRoom.get_or_create_room(self.user1, self.user2)
        room2, created2 = ChatRoom.get_or_create_room(self.user2, self.user1)
        self.assertEqual(room1.id, room2.id)
        self.assertTrue(created1)
        self.assertFalse(created2)
    
    def test_send_message(self):
        """Test d'envoi de message"""
        room, _ = ChatRoom.get_or_create_room(self.user1, self.user2)
        message = Message.objects.create(
            chat_room=room,
            sender=self.user1,
            content="Bonjour!"
        )
        self.assertEqual(message.content, "Bonjour!")
        self.assertFalse(message.is_read)
    
    def test_mark_as_read(self):
        """Test de marquage des messages comme lus"""
        room, _ = ChatRoom.get_or_create_room(self.user1, self.user2)
        message = Message.objects.create(
            chat_room=room,
            sender=self.user1,
            content="Test"
        )
        message.mark_as_read()
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)
    
    def test_user_status(self):
        """Test du statut utilisateur"""
        status, created = UserStatus.objects.get_or_create(user=self.user1)
        self.assertTrue(created)
        self.assertEqual(status.status, 'offline')
        
        status.update_activity()
        self.assertEqual(status.status, 'online')
