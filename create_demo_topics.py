"""
Script pour créer des sujets de démonstration dans le forum
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from forum.models import Category, Topic, Post
from accounts.models import CustomUser

def create_demo_topics():
    """Créer des sujets de démonstration"""
    
    # Vérifier qu'il y a au moins un utilisateur
    try:
        admin = CustomUser.objects.filter(user_type='admin').first()
        if not admin:
            admin = CustomUser.objects.first()
        
        if not admin:
            print("❌ Aucun utilisateur trouvé. Créez d'abord un utilisateur.")
            return
    except:
        print("❌ Erreur lors de la récupération de l'utilisateur")
        return
    
    # Récupérer les catégories
    categories = Category.objects.all()
    if not categories.exists():
        print("❌ Aucune catégorie trouvée. Exécutez d'abord init_forum_categories.py")
        return
    
    # Sujets de démonstration
    demo_topics = [
        {
            'category': 'questions-generales',
            'title': 'Bienvenue sur le forum EduSmart !',
            'content': """# Bienvenue sur le forum EduSmart ! 🎉

Nous sommes ravis de vous accueillir sur notre plateforme de discussion.

## Comment utiliser ce forum ?

1. **Parcourez les catégories** pour trouver le bon endroit pour votre question
2. **Utilisez la recherche** pour voir si votre question n'a pas déjà été posée
3. **Créez un nouveau sujet** avec un titre clair et descriptif
4. **Répondez aux autres** pour créer une communauté d'entraide
5. **Marquez les solutions** qui vous ont aidé

## Règles de bonne conduite

- Soyez respectueux envers tous les membres
- Rédigez des messages clairs et constructifs
- Utilisez les tags appropriés
- Signalez les contenus inappropriés

N'hésitez pas à poser vos questions et à partager vos connaissances ! 💡""",
            'tags': ['bienvenue', 'règles', 'annonce']
        },
        {
            'category': 'aide-aux-cours',
            'title': 'Comment débuter en programmation Python ?',
            'content': """Bonjour à tous,

Je suis complètement débutant en programmation et je voudrais apprendre Python.

**Mes questions :**
- Par où commencer ?
- Quels sont les meilleurs tutoriels pour débuter ?
- Combien de temps faut-il pour avoir des bases solides ?
- Quels projets simples pourrais-je réaliser pour m'entraîner ?

Merci d'avance pour vos conseils ! 🙏""",
            'tags': ['python', 'débutant', 'apprentissage']
        },
        {
            'category': 'technologies-outils',
            'title': 'Comparaison : Django vs Flask pour débutants',
            'content': """Salut la communauté !

Je me demandais quel framework web Python choisir entre Django et Flask.

**Mon contexte :**
- Niveau intermédiaire en Python
- Projet : Application web pour gestion d'une bibliothèque
- Besoin d'un système d'authentification
- Base de données PostgreSQL

**Vos avis ?**
Quels sont les avantages/inconvénients de chacun pour ce type de projet ?

Merci ! 🚀""",
            'tags': ['django', 'flask', 'python', 'web']
        },
        {
            'category': 'projets-travaux',
            'title': 'Projet : Application de gestion de tâches',
            'content': """Bonjour,

Je développe actuellement une application de gestion de tâches (todo list) et j'aimerais avoir vos retours.

**Fonctionnalités actuelles :**
- ✅ Création/modification/suppression de tâches
- ✅ Catégories et tags
- ✅ Dates d'échéance
- ✅ Priorités

**Améliorations prévues :**
- 🔄 Notifications
- 🔄 Collaboration en équipe
- 🔄 Statistiques de productivité

**Questions :**
1. Quelles autres fonctionnalités ajouteriez-vous ?
2. Suggestions pour l'interface utilisateur ?
3. Comment gérer les rappels de manière efficace ?

Je suis ouvert à toutes vos suggestions ! 💪""",
            'tags': ['projet', 'todo', 'collaboration']
        },
        {
            'category': 'conseils-orientation',
            'title': 'Devenir développeur Full-Stack : votre parcours ?',
            'content': """Bonjour à tous,

Je suis actuellement étudiant en informatique et j'aimerais devenir développeur Full-Stack.

**Questions aux développeurs :**
- Quel a été votre parcours ?
- Combien de temps cela vous a pris ?
- Quelles technologies maîtrisez-vous ?
- Conseils pour quelqu'un qui débute ?

Votre expérience m'intéresse beaucoup ! 🎓

Merci pour vos témoignages.""",
            'tags': ['carrière', 'full-stack', 'conseils']
        },
        {
            'category': 'discussions-academiques',
            'title': 'L\'importance de l\'algorithmique dans la programmation moderne',
            'content': """Un sujet de discussion : **L'algorithmique est-elle encore importante aujourd'hui ?**

Avec tous les frameworks et bibliothèques modernes, certains disent que l'algorithmique pure est moins importante.

**Points de débat :**
1. Les frameworks font-ils tout le travail ?
2. Faut-il encore apprendre les algorithmes classiques ?
3. Où l'algorithmique reste-t-elle indispensable ?

**Mon avis :**
Je pense que comprendre les algorithmes aide à écrire du code plus efficace, même avec des frameworks.

Qu'en pensez-vous ? 🤔""",
            'tags': ['algorithmique', 'débat', 'programmation']
        },
        {
            'category': 'suggestions-ameliorations',
            'title': 'Suggestion : Mode sombre pour la plateforme',
            'content': """Salut l'équipe EduSmart ! 👋

J'adore la plateforme, mais je pense qu'un **mode sombre** serait vraiment bienvenu.

**Avantages :**
- Moins de fatigue visuelle lors des sessions de travail tardives
- Économie de batterie sur écrans OLED
- Look moderne et professionnel
- Tendance actuelle dans les applications

**Proposition :**
Bouton de basculement dans la barre de navigation pour switcher entre mode clair/sombre.

Qu'en pensent les autres utilisateurs ? 🌙""",
            'tags': ['suggestion', 'dark-mode', 'ui-ux']
        }
    ]
    
    created_count = 0
    for topic_data in demo_topics:
        category = Category.objects.get(slug=topic_data['category'])
        
        # Vérifier si le sujet existe déjà
        if Topic.objects.filter(title=topic_data['title']).exists():
            print(f"- Le sujet '{topic_data['title']}' existe déjà")
            continue
        
        # Créer le topic
        topic = Topic.objects.create(
            category=category,
            author=admin,
            title=topic_data['title'],
            tags=topic_data['tags']
        )
        
        # Créer le premier post
        Post.objects.create(
            topic=topic,
            author=admin,
            content=topic_data['content']
        )
        
        created_count += 1
        print(f"✓ Sujet créé : {topic.title}")
    
    print(f'\n{created_count} nouveau(x) sujet(s) créé(s)')
    print(f'Total : {Topic.objects.count()} sujets dans le forum')

if __name__ == '__main__':
    print('Création de sujets de démonstration...\n')
    create_demo_topics()
    print('\nTerminé !')
