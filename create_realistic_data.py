"""
Script pour créer des données réalistes pour le forum
"""
import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from forum.models import Category, Topic, Post
from django.contrib.auth import get_user_model

User = get_user_model()

# Titres de topics par catégorie
TOPICS_DATA = {
    'Aide aux Cours': [
        ('Comment résoudre cette équation différentielle ?', 'J\'ai besoin d\'aide avec cette équation du second ordre', 150),
        ('Exercice de physique quantique', 'Quelqu\'un peut m\'expliquer le principe d\'incertitude ?', 200),
        ('Chimie organique - Réaction de substitution', 'Je ne comprends pas les mécanismes SN1 et SN2', 120),
        ('Mathématiques - Intégrales doubles', 'Comment calculer cette intégrale ?', 180),
        ('Aide pour comprendre les séries de Fourier', 'J\'ai du mal avec les transformations', 90),
        ('Question sur les dérivées partielles', 'Exercice de thermodynamique', 110),
        ('Probabilités conditionnelles', 'Je bloque sur cet exercice', 95),
        ('Algèbre linéaire - Espaces vectoriels', 'Aide pour la démonstration', 130),
    ],
    'Projets et Travaux': [
        ('Projet de fin d\'année - Application mobile', 'Qui veut collaborer sur une app éducative ?', 300),
        ('Recherche de partenaires pour hackathon', 'Équipe de 3 personnes cherche un designer', 250),
        ('Projet Machine Learning - Classification', 'Besoin d\'aide pour l\'optimisation', 220),
        ('Développement d\'un site web pour l\'école', 'Stack: React + Django', 280),
        ('Projet IoT - Capteurs intelligents', 'Arduino et Raspberry Pi', 190),
        ('Application de gestion de notes', 'React Native', 160),
        ('Projet blockchain - Smart contracts', 'Solidity et Web3', 140),
    ],
    'Discussions Académiques': [
        ('L\'avenir de l\'intelligence artificielle', 'Débat sur l\'IA générative', 400),
        ('Impact du changement climatique', 'Discussion scientifique', 350),
        ('Théorie de la relativité expliquée simplement', 'Vulgarisation scientifique', 420),
        ('Éthique en recherche scientifique', 'Débat philosophique', 380),
        ('L\'informatique quantique va-t-elle révolutionner le monde ?', 'Discussion technologique', 310),
        ('Neurosciences et conscience', 'Débat scientifique', 290),
    ],
    'Technologies et Outils': [
        ('Meilleurs IDE pour Python en 2025', 'PyCharm vs VSCode vs Jupyter', 500),
        ('GitHub Copilot: retour d\'expérience', 'Utilisation en développement', 450),
        ('Docker vs Kubernetes: quand utiliser quoi ?', 'DevOps', 380),
        ('Les meilleurs frameworks JavaScript', 'React, Vue, Angular comparison', 420),
        ('VS Code: extensions indispensables', 'Productivité', 360),
        ('Git: best practices et workflows', 'Version control', 340),
        ('Bases de données: SQL vs NoSQL', 'MongoDB vs PostgreSQL', 400),
    ],
    'Conseils et Orientation': [
        ('Comment préparer les examens ?', 'Méthodes d\'étude efficaces', 280),
        ('Quelle spécialisation choisir ?', 'IA, cybersécurité ou data science ?', 320),
        ('Stage en entreprise: comment se préparer ?', 'Conseils CV et entretiens', 290),
        ('Master ou école d\'ingénieur ?', 'Orientation après la licence', 310),
        ('Reconversion professionnelle dans l\'IT', 'Témoignages', 260),
    ],
    'Suggestions et Améliorations': [
        ('Améliorer l\'interface du forum', 'Suggestions UX/UI', 180),
        ('Nouvelle fonctionnalité: notifications push', 'Proposition', 160),
        ('Système de badges et récompenses', 'Gamification', 140),
        ('Mode sombre pour le site', 'Amélioration visuelle', 200),
    ],
    'Annonces': [
        ('Nouvelle version de la plateforme disponible', 'Mise à jour majeure', 600),
        ('Conférence sur l\'IA le 15 novembre', 'Event à ne pas manquer', 550),
        ('Maintenance prévue ce weekend', 'Informations importantes', 480),
    ],
    'Questions Générales': [
        ('Comment fonctionne le système de points ?', 'Question sur le forum', 220),
        ('Règles de bonne conduite', 'Netiquette', 190),
        ('Où trouver les ressources pédagogiques ?', 'Aide générale', 210),
        ('Comment signaler un contenu inapproprié ?', 'Modération', 170),
    ],
}

def create_realistic_data():
    print("🔄 Création de données réalistes pour le forum...\n")
    
    # Obtenir ou créer des utilisateurs
    users = list(User.objects.all())
    if len(users) < 3:
        print("❌ Pas assez d'utilisateurs. Créez au moins 3 utilisateurs.")
        return
    
    print(f"✅ {len(users)} utilisateurs disponibles\n")
    
    categories = Category.objects.all()
    
    total_topics_created = 0
    total_posts_created = 0
    
    for category in categories:
        if category.name not in TOPICS_DATA:
            continue
        
        print(f"📁 Catégorie: {category.name}")
        topics_data = TOPICS_DATA[category.name]
        
        for title, content, views in topics_data:
            # Vérifier si le topic existe déjà
            if Topic.objects.filter(title=title, category=category).exists():
                continue
            
            # Créer le topic
            author = random.choice(users)
            days_ago = random.randint(1, 30)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            topic = Topic.objects.create(
                title=title,
                content=content,
                category=category,
                author=author,
                views=views,
                created_at=created_at,
                updated_at=created_at
            )
            
            total_topics_created += 1
            
            # Créer des posts (réponses)
            num_posts = random.randint(3, 15)
            for i in range(num_posts):
                post_author = random.choice([u for u in users if u != author] or users)
                hours_after = random.randint(1, days_ago * 24)
                post_created = created_at + timedelta(hours=hours_after)
                
                post_content = f"Réponse {i+1}: " + random.choice([
                    "Excellente question ! Je pense que...",
                    "J'ai eu le même problème, voici comment je l'ai résolu:",
                    "Je te conseille de regarder cette ressource...",
                    "Merci pour ce sujet intéressant !",
                    "Je ne suis pas d'accord avec cette approche...",
                    "Très bonne analyse ! J'ajouterais que...",
                    "Quelqu'un a-t-il plus d'informations sur ce sujet ?",
                    "Voici mon expérience personnelle:",
                ])
                
                Post.objects.create(
                    topic=topic,
                    author=post_author,
                    content=post_content,
                    created_at=post_created,
                    updated_at=post_created
                )
                
                total_posts_created += 1
        
        print(f"  ✅ {len(topics_data)} topics créés\n")
    
    print("=" * 60)
    print(f"✅ TERMINÉ !")
    print(f"📊 {total_topics_created} nouveaux topics créés")
    print(f"💬 {total_posts_created} nouveaux posts créés")
    print("=" * 60)
    print("\n🎯 Maintenant, entraînez le modèle avec:")
    print("   python manage.py train_category_popularity\n")

if __name__ == '__main__':
    create_realistic_data()
