from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Subject, DifficultyLevel, Quiz, Question, QuizRoom, 
    RoomParticipant, RoomResult, UserProfile
)

User = get_user_model()


class QuizRoomModelTest(TestCase):
    """Tests pour le modèle QuizRoom"""
    
    def setUp(self):
        """Préparation des données de test"""
        # Créer un enseignant
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123',
            user_type='teacher'
        )
        
        # Créer une matière
        self.subject = Subject.objects.create(
            name='Mathématiques',
            slug='mathematiques'
        )
        
        # Créer un niveau de difficulté
        self.difficulty = DifficultyLevel.objects.create(
            name='Moyen',
            level=2,
            points_multiplier=1.5
        )
        
        # Créer un quiz
        self.quiz = Quiz.objects.create(
            title='Quiz Mathématiques',
            slug='quiz-mathematiques',
            subject=self.subject,
            difficulty=self.difficulty,
            created_by=self.teacher,
            status='published'
        )
        
        # Créer une room
        self.room = QuizRoom.objects.create(
            title='Room Test',
            teacher=self.teacher,
            quiz=self.quiz,
            max_participants=50
        )
    
    def test_room_creation(self):
        """Test la création d'une room"""
        self.assertEqual(self.room.title, 'Room Test')
        self.assertEqual(self.room.teacher, self.teacher)
        self.assertEqual(self.room.quiz, self.quiz)
        self.assertIsNotNone(self.room.room_code)
        self.assertEqual(self.room.status, 'waiting')
    
    def test_room_code_generation(self):
        """Test la génération du code de room"""
        self.assertEqual(len(self.room.room_code), 6)
        self.assertTrue(self.room.room_code.isupper())
    
    def test_room_code_uniqueness(self):
        """Test l'unicité du code de room"""
        room2 = QuizRoom.objects.create(
            title='Room Test 2',
            teacher=self.teacher,
            quiz=self.quiz
        )
        self.assertNotEqual(self.room.room_code, room2.room_code)
    
    def test_room_start(self):
        """Test le démarrage d'une room"""
        self.room.start_room()
        self.assertEqual(self.room.status, 'active')
        self.assertIsNotNone(self.room.actual_start)
    
    def test_room_end(self):
        """Test la fin d'une room"""
        self.room.start_room()
        self.room.end_room()
        self.assertEqual(self.room.status, 'completed')
        self.assertIsNotNone(self.room.actual_end)
    
    def test_can_join(self):
        """Test la vérification de participation"""
        self.assertTrue(self.room.can_join())
        
        # Remplir la room
        self.room.max_participants = 1
        self.room.total_participants = 1
        self.room.save()
        self.assertFalse(self.room.can_join())
    
    def test_calculate_grade(self):
        """Test le calcul du grade"""
        self.assertEqual(self.room.calculate_grade(95), 'A+')
        self.assertEqual(self.room.calculate_grade(85), 'A')
        self.assertEqual(self.room.calculate_grade(75), 'B')
        self.assertEqual(self.room.calculate_grade(65), 'C')
        self.assertEqual(self.room.calculate_grade(55), 'D')
        self.assertEqual(self.room.calculate_grade(45), 'F')


class RoomParticipantModelTest(TestCase):
    """Tests pour le modèle RoomParticipant"""
    
    def setUp(self):
        """Préparation des données de test"""
        # Créer un enseignant et un étudiant
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            user_type='teacher'
        )
        self.student = User.objects.create_user(
            username='student1',
            password='testpass123',
            user_type='student'
        )
        
        # Créer les données nécessaires
        self.subject = Subject.objects.create(
            name='Mathématiques',
            slug='mathematiques'
        )
        self.difficulty = DifficultyLevel.objects.create(
            name='Moyen',
            level=2
        )
        self.quiz = Quiz.objects.create(
            title='Quiz Test',
            slug='quiz-test',
            subject=self.subject,
            difficulty=self.difficulty,
            created_by=self.teacher,
            status='published'
        )
        self.room = QuizRoom.objects.create(
            title='Room Test',
            teacher=self.teacher,
            quiz=self.quiz
        )
        
        # Créer un participant
        self.participant = RoomParticipant.objects.create(
            room=self.room,
            student=self.student
        )
    
    def test_participant_creation(self):
        """Test la création d'un participant"""
        self.assertEqual(self.participant.room, self.room)
        self.assertEqual(self.participant.student, self.student)
        self.assertEqual(self.participant.status, 'joined')
    
    def test_participant_start_quiz(self):
        """Test le démarrage du quiz pour un participant"""
        self.participant.start_quiz()
        self.assertEqual(self.participant.status, 'in_progress')
        self.assertIsNotNone(self.participant.started_at)
    
    def test_participant_complete_quiz(self):
        """Test la fin du quiz pour un participant"""
        self.participant.start_quiz()
        self.participant.complete_quiz()
        self.assertEqual(self.participant.status, 'completed')
        self.assertIsNotNone(self.participant.completed_at)


class RoomResultModelTest(TestCase):
    """Tests pour le modèle RoomResult"""
    
    def setUp(self):
        """Préparation des données de test"""
        # Créer les données nécessaires
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            user_type='teacher'
        )
        self.student = User.objects.create_user(
            username='student1',
            password='testpass123',
            user_type='student'
        )
        
        self.subject = Subject.objects.create(
            name='Mathématiques',
            slug='mathematiques'
        )
        self.difficulty = DifficultyLevel.objects.create(
            name='Moyen',
            level=2
        )
        self.quiz = Quiz.objects.create(
            title='Quiz Test',
            slug='quiz-test',
            subject=self.subject,
            difficulty=self.difficulty,
            created_by=self.teacher,
            status='published',
            points_available=100
        )
        self.room = QuizRoom.objects.create(
            title='Room Test',
            teacher=self.teacher,
            quiz=self.quiz
        )
        self.participant = RoomParticipant.objects.create(
            room=self.room,
            student=self.student
        )
        
        # Créer un résultat
        self.result = RoomResult.objects.create(
            participant=self.participant,
            score=85,
            percentage=85,
            grade='A',
            correct_answers=17,
            wrong_answers=3,
            total_questions=20,
            time_taken=1200,
            points_earned=127,
            experience_earned=85
        )
    
    def test_result_creation(self):
        """Test la création d'un résultat"""
        self.assertEqual(self.result.score, 85)
        self.assertEqual(self.result.percentage, 85)
        self.assertEqual(self.result.grade, 'A')
    
    def test_result_accuracy_rate(self):
        """Test le calcul du taux de précision"""
        accuracy = self.result.get_accuracy_rate()
        self.assertEqual(accuracy, 85.0)
    
    def test_result_time_display(self):
        """Test l'affichage du temps"""
        time_display = self.result.get_time_taken_display()
        self.assertEqual(time_display, '20m 0s')
    
    def test_result_is_passed(self):
        """Test la vérification de réussite"""
        self.quiz.passing_score = 60
        self.quiz.save()
        self.assertTrue(self.result.is_passed())
        
        self.quiz.passing_score = 90
        self.quiz.save()
        self.assertFalse(self.result.is_passed())


class RoomViewsTest(TestCase):
    """Tests pour les vues des rooms"""
    
    def setUp(self):
        """Préparation des données de test"""
        self.client = Client()
        
        # Créer un enseignant et un étudiant
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            user_type='teacher'
        )
        self.student = User.objects.create_user(
            username='student1',
            password='testpass123',
            user_type='student'
        )
        
        # Créer les données nécessaires
        self.subject = Subject.objects.create(
            name='Mathématiques',
            slug='mathematiques'
        )
        self.difficulty = DifficultyLevel.objects.create(
            name='Moyen',
            level=2
        )
        self.quiz = Quiz.objects.create(
            title='Quiz Test',
            slug='quiz-test',
            subject=self.subject,
            difficulty=self.difficulty,
            created_by=self.teacher,
            status='published'
        )
    
    def test_teacher_room_dashboard_access(self):
        """Test l'accès au tableau de bord enseignant"""
        self.client.login(username='teacher1', password='testpass123')
        response = self.client.get('/gamification/teacher/rooms/')
        self.assertEqual(response.status_code, 200)
    
    def test_student_room_list_access(self):
        """Test l'accès à la liste des rooms étudiant"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get('/gamification/student/rooms/')
        self.assertEqual(response.status_code, 200)
    
    def test_join_room_with_code(self):
        """Test la participation à une room avec code"""
        # Créer une room
        room = QuizRoom.objects.create(
            title='Room Test',
            teacher=self.teacher,
            quiz=self.quiz
        )
        
        # Se connecter en tant qu'étudiant
        self.client.login(username='student1', password='testpass123')
        
        # Rejoindre la room
        response = self.client.post('/gamification/student/room/join/', {
            'room_code': room.room_code
        })
        
        # Vérifier que le participant a été créé
        self.assertTrue(
            RoomParticipant.objects.filter(
                room=room,
                student=self.student
            ).exists()
        )

