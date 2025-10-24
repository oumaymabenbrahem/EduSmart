"""
Script pour initialiser les catégories du forum
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from forum.models import Category

def create_initial_categories():
    """Créer les catégories initiales du forum"""
    
    categories_data = [
        {
            'name': 'Questions Générales',
            'slug': 'questions-generales',
            'description': 'Posez toutes vos questions générales sur la plateforme et l\'apprentissage.',
            'icon': 'bi-question-circle',
            'order': 1
        },
        {
            'name': 'Aide aux Cours',
            'slug': 'aide-aux-cours',
            'description': 'Demandez de l\'aide sur les cours, les exercices et les devoirs.',
            'icon': 'bi-book',
            'order': 2
        },
        {
            'name': 'Projets et Travaux',
            'slug': 'projets-travaux',
            'description': 'Partagez vos projets, collaborez et obtenez des retours.',
            'icon': 'bi-folder',
            'order': 3
        },
        {
            'name': 'Discussions Académiques',
            'slug': 'discussions-academiques',
            'description': 'Débats et discussions sur des sujets académiques variés.',
            'icon': 'bi-chat-dots',
            'order': 4
        },
        {
            'name': 'Technologies et Outils',
            'slug': 'technologies-outils',
            'description': 'Parlez des technologies, langages de programmation et outils de développement.',
            'icon': 'bi-code-slash',
            'order': 5
        },
        {
            'name': 'Conseils et Orientation',
            'slug': 'conseils-orientation',
            'description': 'Conseils de carrière, orientation et parcours professionnel.',
            'icon': 'bi-compass',
            'order': 6
        },
        {
            'name': 'Suggestions et Améliorations',
            'slug': 'suggestions-ameliorations',
            'description': 'Proposez des améliorations pour la plateforme EduSmart.',
            'icon': 'bi-lightbulb',
            'order': 7
        },
        {
            'name': 'Annonces',
            'slug': 'annonces',
            'description': 'Annonces officielles et informations importantes.',
            'icon': 'bi-megaphone',
            'order': 0
        },
    ]
    
    created_count = 0
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults={
                'name': cat_data['name'],
                'description': cat_data['description'],
                'icon': cat_data['icon'],
                'order': cat_data['order']
            }
        )
        if created:
            created_count += 1
            print(f'✓ Catégorie créée : {category.name}')
        else:
            print(f'- Catégorie existe déjà : {category.name}')
    
    print(f'\n{created_count} nouvelle(s) catégorie(s) créée(s)')
    print(f'Total : {Category.objects.count()} catégories')

if __name__ == '__main__':
    print('Initialisation des catégories du forum...\n')
    create_initial_categories()
    print('\nTerminé !')
