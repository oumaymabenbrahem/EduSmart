# Commandes Utiles - Système de Rooms

## 🚀 Démarrage

### Installation Initiale
```bash
# Appliquer les migrations
python manage.py migrate gamification

# Créer un superutilisateur
python manage.py createsuperuser

# Démarrer le serveur
python manage.py runserver
```

### Accès
```
Admin: http://localhost:8000/admin/
Enseignant: http://localhost:8000/gamification/teacher/rooms/
Étudiant: http://localhost:8000/gamification/student/rooms/
```

## 🧪 Tests

### Exécuter Tous les Tests
```bash
python manage.py test gamification.tests_room -v 2
```

### Exécuter un Test Spécifique
```bash
# Test du modèle QuizRoom
python manage.py test gamification.tests_room.QuizRoomModelTest -v 2

# Test d'une méthode spécifique
python manage.py test gamification.tests_room.QuizRoomModelTest.test_room_creation -v 2
```

### Exécuter avec Couverture
```bash
# Installer coverage
pip install coverage

# Exécuter les tests avec couverture
coverage run --source='gamification' manage.py test gamification.tests_room

# Afficher le rapport
coverage report

# Générer un rapport HTML
coverage html
```

## 📊 Gestion de la Base de Données

### Migrations

#### Créer une Migration
```bash
python manage.py makemigrations gamification
```

#### Appliquer les Migrations
```bash
python manage.py migrate gamification
```

#### Voir l'État des Migrations
```bash
python manage.py showmigrations gamification
```

#### Annuler une Migration
```bash
# Annuler la dernière migration
python manage.py migrate gamification 0001

# Annuler toutes les migrations
python manage.py migrate gamification zero
```

### Données

#### Créer des Données de Test
```bash
python manage.py shell

# Dans le shell Django
from django.contrib.auth import get_user_model
from gamification.models import QuizRoom, Quiz

User = get_user_model()

# Créer un enseignant
teacher = User.objects.create_user(
    username='teacher1',
    email='teacher@example.com',
    password='password123',
    is_staff=True
)

# Créer un étudiant
student = User.objects.create_user(
    username='student1',
    email='student@example.com',
    password='password123'
)

# Créer une room
quiz = Quiz.objects.first()
room = QuizRoom.objects.create(
    title='Quiz Test',
    teacher=teacher,
    quiz=quiz
)

print(f"Room créée: {room.room_code}")
```

#### Supprimer Toutes les Données
```bash
python manage.py flush gamification
```

#### Exporter les Données
```bash
# Exporter en JSON
python manage.py dumpdata gamification > gamification_data.json

# Exporter un modèle spécifique
python manage.py dumpdata gamification.QuizRoom > rooms.json
```

#### Importer les Données
```bash
python manage.py loaddata gamification_data.json
```

## 🔍 Inspection

### Shell Django
```bash
python manage.py shell

# Lister toutes les rooms
from gamification.models import QuizRoom
rooms = QuizRoom.objects.all()
for room in rooms:
    print(f"{room.title} ({room.room_code}) - {room.status}")

# Lister les participants d'une room
room = QuizRoom.objects.get(room_code='ABC123')
participants = room.participants.all()
for p in participants:
    print(f"{p.student.username} - {p.status}")

# Lister les résultats
from gamification.models import RoomResult
results = RoomResult.objects.filter(participant__room=room).order_by('rank')
for r in results:
    print(f"{r.rank}. {r.participant.student.username} - {r.grade}")
```

### Requêtes SQL
```bash
# Voir les requêtes SQL
python manage.py shell

from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as context:
    rooms = QuizRoom.objects.all()
    for room in rooms:
        print(room.title)

print(f"Nombre de requêtes: {len(context)}")
for query in context:
    print(query['sql'])
```

## 📈 Statistiques

### Compter les Objets
```bash
python manage.py shell

from gamification.models import QuizRoom, RoomParticipant, RoomResult

print(f"Rooms: {QuizRoom.objects.count()}")
print(f"Participants: {RoomParticipant.objects.count()}")
print(f"Résultats: {RoomResult.objects.count()}")
```

### Statistiques par Room
```bash
python manage.py shell

from gamification.models import QuizRoom

room = QuizRoom.objects.get(room_code='ABC123')
print(f"Room: {room.title}")
print(f"Participants: {room.participants.count()}")
print(f"Résultats: {room.results.count()}")
print(f"Score moyen: {room.average_score()}")
```

## 🔧 Maintenance

### Nettoyer les Données Obsolètes
```bash
python manage.py shell

from gamification.models import QuizRoom
from django.utils import timezone
from datetime import timedelta

# Supprimer les rooms terminées il y a plus de 30 jours
cutoff_date = timezone.now() - timedelta(days=30)
old_rooms = QuizRoom.objects.filter(
    status='completed',
    updated_at__lt=cutoff_date
)
count = old_rooms.count()
old_rooms.delete()
print(f"Supprimé {count} rooms")
```

### Vérifier l'Intégrité des Données
```bash
python manage.py shell

from gamification.models import QuizRoom, RoomParticipant, RoomResult

# Vérifier que tous les résultats ont un participant
orphaned_results = RoomResult.objects.filter(participant__isnull=True)
print(f"Résultats orphelins: {orphaned_results.count()}")

# Vérifier que tous les participants ont une room
orphaned_participants = RoomParticipant.objects.filter(room__isnull=True)
print(f"Participants orphelins: {orphaned_participants.count()}")
```

## 📱 Développement

### Serveur de Développement
```bash
# Démarrer avec rechargement automatique
python manage.py runserver

# Démarrer sur un port spécifique
python manage.py runserver 8001

# Démarrer sur une adresse spécifique
python manage.py runserver 0.0.0.0:8000
```

### Débogage
```bash
# Ajouter des points d'arrêt dans le code
import pdb; pdb.set_trace()

# Ou utiliser ipdb (plus beau)
import ipdb; ipdb.set_trace()
```

### Logs
```bash
# Voir les logs Django
python manage.py runserver --verbosity=2

# Voir les logs de la base de données
# Ajouter dans settings.py:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 🚀 Déploiement

### Préparation
```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Vérifier la configuration
python manage.py check --deploy

# Exécuter les tests
python manage.py test gamification.tests_room
```

### Production
```bash
# Démarrer avec Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Démarrer avec Daphne (ASGI)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

## 📊 Monitoring

### Vérifier la Santé
```bash
python manage.py shell

from django.core.management import call_command
call_command('check')
```

### Voir les Migrations Appliquées
```bash
python manage.py showmigrations gamification
```

### Voir les Modèles
```bash
python manage.py inspectdb
```

## 🔐 Sécurité

### Changer les Secrets
```bash
# Générer une nouvelle SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Vérifier la Sécurité
```bash
python manage.py check --deploy
```

## 📚 Documentation

### Générer la Documentation
```bash
# Installer Sphinx
pip install sphinx

# Créer la documentation
sphinx-quickstart docs

# Générer le HTML
cd docs
make html
```

## 🐛 Dépannage

### Erreur de Migration
```bash
# Voir l'état des migrations
python manage.py showmigrations

# Annuler et refaire
python manage.py migrate gamification 0001
python manage.py migrate gamification
```

### Erreur de Permissions
```bash
# Vérifier les permissions
python manage.py shell

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from gamification.models import QuizRoom

content_type = ContentType.objects.get_for_model(QuizRoom)
permissions = Permission.objects.filter(content_type=content_type)
for perm in permissions:
    print(perm)
```

### Erreur de Cache
```bash
# Vider le cache
python manage.py shell

from django.core.cache import cache
cache.clear()
```

## 📝 Commandes Personnalisées

### Créer une Commande Personnalisée
```bash
# Créer le fichier
touch gamification/management/commands/create_test_rooms.py

# Contenu:
from django.core.management.base import BaseCommand
from gamification.models import QuizRoom
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée des rooms de test'

    def handle(self, *args, **options):
        teacher = User.objects.get(username='teacher1')
        for i in range(5):
            QuizRoom.objects.create(
                title=f'Room Test {i+1}',
                teacher=teacher
            )
        self.stdout.write('Rooms créées!')
```

### Exécuter la Commande
```bash
python manage.py create_test_rooms
```

## 🎯 Workflow Complet

### Développement
```bash
# 1. Créer une branche
git checkout -b feature/new-feature

# 2. Faire les changements
# ... éditer les fichiers ...

# 3. Exécuter les tests
python manage.py test gamification.tests_room

# 4. Commiter
git add .
git commit -m "Ajouter nouvelle fonctionnalité"

# 5. Pousser
git push origin feature/new-feature
```

### Déploiement
```bash
# 1. Vérifier les tests
python manage.py test gamification.tests_room

# 2. Collecter les statiques
python manage.py collectstatic --noinput

# 3. Appliquer les migrations
python manage.py migrate gamification

# 4. Démarrer le serveur
gunicorn config.wsgi:application
```

---

**Dernière mise à jour**: 2025-10-25
**Version**: 1.0

