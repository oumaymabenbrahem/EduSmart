# Guide de Démarrage Rapide - Système de Rooms

## 🚀 Installation

### 1. Appliquer les migrations
```bash
python manage.py migrate gamification
```

### 2. Créer un superutilisateur (si nécessaire)
```bash
python manage.py createsuperuser
```

### 3. Démarrer le serveur
```bash
python manage.py runserver
```

## 👨‍🏫 Pour les Enseignants

### Étape 1: Accéder au Tableau de Bord
```
URL: http://localhost:8000/gamification/teacher/rooms/
```

### Étape 2: Créer une Room

#### Option A: Avec un Quiz Existant
1. Cliquez sur "Créer une Room"
2. Remplissez le formulaire:
   - Titre: "Quiz Mathématiques - Chapitre 5"
   - Description: "Quiz sur les équations"
   - Sélectionnez un quiz
   - Configurez les options
3. Cliquez sur "Créer la Room"
4. Notez le code généré (ex: ABC123)

#### Option B: Avec Quiz IA
1. Cliquez sur "Créer avec IA"
2. Remplissez le formulaire:
   - Titre de la room
   - Sujet (ex: Mathématiques)
   - Difficulté (1-5)
   - Nombre de questions (5-50)
   - Durée limite
3. Cliquez sur "Générer et Créer la Room"
4. Le quiz est généré automatiquement

### Étape 3: Partager le Code
- Partagez le code (ex: ABC123) avec vos étudiants
- Via email, SMS, ou affichage en classe

### Étape 4: Démarrer la Room
1. Attendez que les étudiants rejoignent
2. Cliquez sur "Démarrer la Room"
3. Les étudiants peuvent maintenant commencer le quiz

### Étape 5: Monitorer les Résultats
- Consultez le tableau de bord en temps réel
- Voyez les participants et leurs scores
- Analysez les résultats

### Étape 6: Terminer la Room
1. Cliquez sur "Terminer la Room"
2. Les résultats sont finalisés
3. Consultez les statistiques complètes

## 👨‍🎓 Pour les Étudiants

### Étape 1: Rejoindre une Room
```
URL: http://localhost:8000/gamification/student/room/join/
```

### Étape 2: Entrer le Code
1. Entrez le code fourni par l'enseignant
2. Cliquez sur "Rejoindre"
3. Attendez le démarrage de la room

### Étape 3: Passer le Quiz
1. Cliquez sur "Commencer le Quiz"
2. Répondez aux questions
3. Utilisez le timer pour gérer votre temps
4. Cliquez sur "Soumettre le Quiz"

### Étape 4: Voir les Résultats
- Consultez votre score et grade
- Voyez les badges gagnés
- Consultez le classement
- Révisez vos réponses (si autorisé)

## 📊 Exemples de Codes

### Créer une Room Programmatiquement

```python
from gamification.models import QuizRoom, Quiz
from django.contrib.auth import get_user_model

User = get_user_model()

# Récupérer l'enseignant et le quiz
teacher = User.objects.get(username='teacher1')
quiz = Quiz.objects.get(slug='quiz-mathematiques')

# Créer la room
room = QuizRoom.objects.create(
    title='Quiz Mathématiques - Session 1',
    description='Quiz sur les équations',
    teacher=teacher,
    quiz=quiz,
    max_participants=50,
    time_limit_override=30,
    show_results_immediately=True,
    allow_review=True,
    show_leaderboard=True,
    enable_badges=True
)

print(f"Room créée avec le code: {room.room_code}")
```

### Rejoindre une Room Programmatiquement

```python
from gamification.models import QuizRoom, RoomParticipant
from django.contrib.auth import get_user_model

User = get_user_model()

# Récupérer la room et l'étudiant
room = QuizRoom.objects.get(room_code='ABC123')
student = User.objects.get(username='student1')

# Créer la participation
participant, created = RoomParticipant.objects.get_or_create(
    room=room,
    student=student
)

if created:
    print(f"Étudiant {student.username} a rejoint la room")
else:
    print(f"Étudiant {student.username} était déjà dans la room")
```

### Démarrer un Quiz

```python
from gamification.models import RoomParticipant, QuizAttempt

# Récupérer le participant
participant = RoomParticipant.objects.get(id=1)

# Créer une tentative de quiz
attempt = QuizAttempt.objects.create(
    student=participant.student,
    quiz=participant.room.quiz,
    attempt_number=1,
    status='in_progress'
)

# Lier la tentative au participant
participant.quiz_attempt = attempt
participant.start_quiz()

print(f"Quiz démarré pour {participant.student.username}")
```

### Soumettre les Réponses

```python
from gamification.models import RoomResult, RoomParticipant
from django.utils import timezone

# Récupérer le participant
participant = RoomParticipant.objects.get(id=1)
quiz_attempt = participant.quiz_attempt

# Simuler les réponses
answers = {
    '1': 'A',
    '2': 'B',
    '3': 'C',
}

# Calculer le score
correct_count = 3
total_questions = 3
percentage = (correct_count / total_questions) * 100

# Créer le résultat
result = RoomResult.objects.create(
    participant=participant,
    score=correct_count * 10,
    percentage=percentage,
    grade=participant.room.calculate_grade(percentage),
    correct_answers=correct_count,
    wrong_answers=0,
    total_questions=total_questions,
    time_taken=600,
    points_earned=30,
    experience_earned=100
)

# Marquer le participant comme terminé
participant.complete_quiz()

print(f"Résultats soumis: {result.grade} ({result.percentage}%)")
```

## 🔍 Vérification

### Vérifier les Rooms Créées
```python
from gamification.models import QuizRoom

# Lister toutes les rooms
rooms = QuizRoom.objects.all()
for room in rooms:
    print(f"{room.title} ({room.room_code}) - {room.status}")
```

### Vérifier les Participants
```python
from gamification.models import RoomParticipant

# Lister les participants d'une room
room = QuizRoom.objects.get(room_code='ABC123')
participants = room.participants.all()
for p in participants:
    print(f"{p.student.username} - {p.status}")
```

### Vérifier les Résultats
```python
from gamification.models import RoomResult

# Lister les résultats d'une room
room = QuizRoom.objects.get(room_code='ABC123')
results = RoomResult.objects.filter(participant__room=room).order_by('rank')
for r in results:
    print(f"{r.rank}. {r.participant.student.username} - {r.grade} ({r.percentage}%)")
```

## 🧪 Tests

### Exécuter les Tests
```bash
python manage.py test gamification.tests_room -v 2
```

### Résultats Attendus
```
Ran 17 tests in X.XXXs
OK
```

## 📱 URLs Principales

### Enseignant
- Dashboard: `/gamification/teacher/rooms/`
- Créer: `/gamification/teacher/room/create/`
- Créer avec IA: `/gamification/teacher/room/create-ai/`
- Détails: `/gamification/teacher/room/<code>/`

### Étudiant
- Mes Rooms: `/gamification/student/rooms/`
- Rejoindre: `/gamification/student/room/join/`
- Détails: `/gamification/room/<code>/`
- Quiz: `/gamification/room/<code>/quiz/`
- Résultats: `/gamification/room/<code>/result/`
- Classement: `/gamification/room/<code>/leaderboard/`

## 🐛 Dépannage

### Le code ne fonctionne pas
- Vérifiez que le code est correct (6 caractères)
- Vérifiez que la room existe
- Vérifiez que vous êtes connecté

### Je ne vois pas mes résultats
- Vérifiez que vous avez soumis le quiz
- Vérifiez que la room est terminée
- Actualisez la page

### Les badges ne s'affichent pas
- Vérifiez que `enable_badges` est activé
- Vérifiez que vous avez atteint les critères
- Consultez les logs pour les erreurs

## 📞 Support

Pour plus d'aide:
1. Consultez `ROOM_SYSTEM_GUIDE.md`
2. Consultez `IMPLEMENTATION_SUMMARY.md`
3. Vérifiez les tests dans `gamification/tests_room.py`
4. Consultez le code source avec commentaires

## ✨ Prochaines Étapes

1. Personnalisez les templates selon votre design
2. Ajoutez des notifications
3. Intégrez avec votre système d'authentification
4. Configurez les badges personnalisés
5. Mettez en place les recommandations d'apprentissage

