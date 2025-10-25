# Guide du Système de Rooms de Quiz - EduSmart

## Vue d'ensemble

Le système de Rooms de Quiz permet aux enseignants de créer des sessions de quiz interactives et de partager des codes avec leurs étudiants. Les étudiants peuvent rejoindre les rooms avec un code et passer le quiz en temps réel.

## Fonctionnalités Principales

### 1. **Création de Rooms (Enseignants)**

#### Option 1: Créer une Room avec un Quiz Existant
- Accédez à: `/gamification/teacher/rooms/`
- Cliquez sur "Créer une Room"
- Sélectionnez un quiz existant
- Configurez les paramètres (durée, nombre max de participants, etc.)
- La room génère automatiquement un code unique (ex: ABC123)

#### Option 2: Créer une Room avec Quiz IA
- Accédez à: `/gamification/teacher/rooms/`
- Cliquez sur "Créer avec IA"
- Spécifiez le sujet, la difficulté et le nombre de questions
- Le système génère automatiquement un quiz riche
- La room est créée avec le quiz généré

### 2. **Gestion des Rooms (Enseignants)**

#### Tableau de Bord
- Vue d'ensemble de toutes les rooms créées
- Statistiques: nombre de participants, score moyen, statut
- Actions rapides: démarrer, terminer, voir les détails

#### Statuts de Room
- **En attente**: Room créée, en attente de démarrage
- **Active**: Room en cours, les étudiants peuvent passer le quiz
- **Terminée**: Room fermée, résultats finalisés
- **Annulée**: Room supprimée

#### Contrôles
- **Démarrer**: Passer la room en mode actif
- **Terminer**: Fermer la room et finaliser les résultats
- **Voir les détails**: Afficher les résultats et les participants

### 3. **Rejoindre une Room (Étudiants)**

#### Processus
1. Accédez à: `/gamification/student/room/join/`
2. Entrez le code fourni par l'enseignant
3. Cliquez sur "Rejoindre"
4. Attendez que l'enseignant démarre la room
5. Cliquez sur "Commencer le Quiz"

#### Code de Room
- Format: 6 caractères alphanumériques (ex: ABC123)
- Unique pour chaque room
- Partageable avec les étudiants

### 4. **Passer le Quiz**

#### Interface de Quiz
- Affichage du timer en temps réel
- Barre de progression
- Questions avec options de réponse
- Support de plusieurs types de questions:
  - Choix multiples
  - Vrai/Faux
  - Réponses courtes

#### Fonctionnalités
- **Timer**: Compte à rebours automatique
- **Progression**: Suivi du nombre de questions répondues
- **Sauvegarde automatique**: Les réponses sont sauvegardées
- **Soumission**: Bouton pour soumettre les réponses

### 5. **Résultats et Badges**

#### Affichage des Résultats
- **Grade**: A+, A, B, C, D, F basé sur le pourcentage
- **Pourcentage**: Score en pourcentage
- **Points**: Points gagnés
- **Expérience**: Points d'expérience gagnés
- **Temps**: Temps total pris
- **Classement**: Position dans la room

#### Badges
- Attribués automatiquement selon les performances
- Affichés avec icône et description
- Contribuent aux points de gamification

#### Classement
- Affichage du top 10 des participants
- Classement complet disponible
- Trophées pour les 3 premiers

### 6. **Analyse des Résultats (Enseignants)**

#### Tableau de Résultats
- Liste de tous les participants
- Scores et pourcentages
- Grades et classements
- Badges gagnés
- Temps pris

#### Statistiques
- Score moyen de la room
- Nombre de participants terminés
- Taux de réussite

## Modèles de Données

### QuizRoom
```python
- title: Titre de la room
- room_code: Code unique (6 caractères)
- teacher: Enseignant créateur
- quiz: Quiz associé
- status: Statut (waiting, active, completed, cancelled)
- total_participants: Nombre de participants
- average_score: Score moyen
- max_participants: Limite de participants
- time_limit_override: Durée personnalisée
- show_results_immediately: Afficher résultats immédiatement
- allow_review: Permettre la révision
- show_leaderboard: Afficher le classement
- enable_badges: Activer les badges
```

### RoomParticipant
```python
- room: Room associée
- student: Étudiant participant
- status: Statut (joined, in_progress, completed, abandoned)
- quiz_attempt: Tentative de quiz liée
- joined_at: Date de participation
- started_at: Date de début
- completed_at: Date de fin
```

### RoomResult
```python
- participant: Participant
- score: Score obtenu
- percentage: Pourcentage
- grade: Grade (A+, A, B, C, D, F)
- rank: Classement
- correct_answers: Réponses correctes
- wrong_answers: Réponses incorrectes
- skipped_answers: Réponses sautées
- time_taken: Temps pris (secondes)
- points_earned: Points gagnés
- experience_earned: Expérience gagnée
- badges_earned: Badges gagnés
- easy_correct: Questions faciles correctes
- medium_correct: Questions moyennes correctes
- hard_correct: Questions difficiles correctes
```

## URLs

### Enseignant
- `GET /gamification/teacher/rooms/` - Tableau de bord
- `GET /gamification/teacher/room/create/` - Créer une room
- `POST /gamification/teacher/room/create/` - Soumettre la création
- `GET /gamification/teacher/room/create-ai/` - Créer avec IA
- `POST /gamification/teacher/room/create-ai/` - Soumettre la création IA
- `GET /gamification/teacher/room/<code>/` - Détails de la room
- `GET /gamification/teacher/room/<code>/start/` - Démarrer la room
- `GET /gamification/teacher/room/<code>/end/` - Terminer la room
- `POST /gamification/teacher/room/<code>/delete/` - Supprimer la room

### Étudiant
- `GET /gamification/student/rooms/` - Mes rooms
- `GET /gamification/student/room/join/` - Rejoindre une room
- `POST /gamification/student/room/join/` - Soumettre le code
- `GET /gamification/room/<code>/` - Détails de la room
- `GET /gamification/room/<code>/start/` - Démarrer le quiz
- `GET /gamification/room/<code>/quiz/` - Interface du quiz
- `POST /gamification/room/<code>/submit/` - Soumettre les réponses
- `GET /gamification/room/<code>/result/` - Résultats
- `GET /gamification/room/<code>/leaderboard/` - Classement complet

## Flux d'Utilisation

### Enseignant
1. Créer une room (avec quiz existant ou IA)
2. Partager le code avec les étudiants
3. Attendre que les étudiants rejoignent
4. Démarrer la room
5. Monitorer les résultats en temps réel
6. Terminer la room
7. Analyser les résultats

### Étudiant
1. Recevoir le code de la room
2. Rejoindre la room avec le code
3. Attendre le démarrage
4. Commencer le quiz
5. Répondre aux questions
6. Soumettre les réponses
7. Voir les résultats et badges
8. Consulter le classement

## Calcul des Grades

- **A+**: 90-100%
- **A**: 80-89%
- **B**: 70-79%
- **C**: 60-69%
- **D**: 50-59%
- **F**: <50%

## Sécurité

- Vérification de l'authentification pour toutes les vues
- Vérification du rôle (enseignant/étudiant)
- Validation du code de room
- Vérification de la participation
- Protection CSRF sur tous les formulaires

## Améliorations Futures

- [ ] Notifications en temps réel
- [ ] Chat en direct pendant le quiz
- [ ] Statistiques avancées par question
- [ ] Export des résultats (PDF, Excel)
- [ ] Feedback personnalisé par question
- [ ] Recommandations d'apprentissage
- [ ] Comparaison avec les performances précédentes
- [ ] Analyse des points faibles

