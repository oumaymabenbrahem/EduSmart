"""
Module de modération de contenu par Intelligence Artificielle
Utilise Google Perspective API (100% GRATUIT, 1M requêtes/jour)
"""

import os
from typing import Dict, Any, Optional
from django.conf import settings


# Catégories de contenu inapproprié
CATEGORIES_FR = {
    'TOXICITY': 'Toxicité',
    'SEVERE_TOXICITY': 'Toxicité sévère',
    'IDENTITY_ATTACK': 'Attaque identitaire',
    'INSULT': 'Insulte',
    'PROFANITY': 'Vulgarité',
    'THREAT': 'Menace',
    'SEXUALLY_EXPLICIT': 'Contenu sexuel explicite',
    'FLIRTATION': 'Drague',
}


def verifier_contenu_perspective(texte: str) -> Dict[str, Any]:
    """
    Vérifie si le contenu est approprié en utilisant Google Perspective API (GRATUIT)
    
    Args:
        texte: Le texte à vérifier
    
    Returns:
        Dict contenant:
        - 'accepte': bool
        - 'score': float (0-1)
        - 'categories': list
        - 'details': dict
    """
    
    # Vérifier si Perspective est configuré
    perspective_key = getattr(settings, 'PERSPECTIVE_API_KEY', None)
    
    if not perspective_key:
        # Mode dégradé : accepter sans clé
        return {
            'accepte': True,
            'score': 0.0,
            'categories': [],
            'details': {},
            'message': 'Modération IA désactivée (pas de clé API)'
        }
    
    try:
        from googleapiclient import discovery
        
        # Créer le client Perspective
        client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=perspective_key,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )
        
        # Analyser le texte
        analyze_request = {
            'comment': {'text': texte},
            'languages': ['fr', 'en'],
            'requestedAttributes': {
                'TOXICITY': {},
                'SEVERE_TOXICITY': {},
                'IDENTITY_ATTACK': {},
                'INSULT': {},
                'PROFANITY': {},
                'THREAT': {},
            }
        }
        
        response = client.comments().analyze(body=analyze_request).execute()
        
        # Extraire les scores
        scores = {}
        categories_detectees = []
        max_score = 0.0
        
        for attr_name, attr_data in response.get('attributeScores', {}).items():
            score = attr_data['summaryScore']['value']
            scores[attr_name] = score
            
            if score > max_score:
                max_score = score
            
            # Seuil personnalisable
            seuil = getattr(settings, 'AI_MODERATION_THRESHOLD', 0.7)
            
            if score >= seuil:
                categories_detectees.append({
                    'nom': attr_name,
                    'nom_fr': CATEGORIES_FR.get(attr_name, attr_name),
                    'score': score
                })
        
        # Déterminer si le contenu est acceptable
        seuil_global = getattr(settings, 'AI_MODERATION_THRESHOLD', 0.7)
        accepte = max_score < seuil_global
        
        return {
            'accepte': accepte,
            'score': max_score,
            'categories': categories_detectees,
            'details': {
                'scores': scores
            },
            'message': None if accepte else 'Contenu potentiellement inapproprié détecté'
        }
        
    except ImportError:
        # Bibliothèque Google non installée
        return {
            'accepte': True,
            'score': 0.0,
            'categories': [],
            'details': {},
            'message': 'Bibliothèque Google API non installée'
        }
    
    except Exception as e:
        # En cas d'erreur, accepter le contenu (mode permissif)
        print(f"Erreur lors de la modération IA: {str(e)}")
        return {
            'accepte': True,  # ⬅️ Accepte si erreur (change en False pour être strict)
            'score': 0.0,
            'categories': [],
            'details': {'error': str(e)},
            'message': f'Service de modération temporairement indisponible'
        }


# Alias pour compatibilité avec le code existant
verifier_contenu_openai = verifier_contenu_perspective


def _local_profanity_check(texte: str) -> Dict[str, Any]:
    """
    Vérification locale basique (fallback) pour capter les gros mots évidents
    sans appeler une API externe. Couvre un ensemble simple de mots en anglais
    et en français.
    Retourne le même format dict que les fonctions de modération.
    """
    import re

    # Liste de gros mots / insultes (anglais et français)
    profanities = [
        # Anglais - Niveau fort
        r"fuck",
        r"fucking",
        r"fucker",
        r"motherfucker",
        r"shit",
        r"shitty",
        r"bullshit",
        r"bitch",
        r"bastard",
        r"asshole",
        r"ass",
        r"damn",
        r"cunt",
        r"whore",
        r"slut",
        r"dick",
        r"cock",
        r"pussy",
        r"retard",
        r"retarded",
        r"fag",
        r"faggot",
        r"nigger",
        r"nigga",
        
        # Anglais - Insultes courantes
        r"idiot",
        r"stupid",
        r"dumb",
        r"moron",
        r"imbecile",
        r"loser",
        r"jackass",
        r"douche",
        r"douchebag",
        r"scumbag",
        r"jerk",
        
        # Français - Niveau fort
        r"connard",
        r"connasse",
        r"enculé",
        r"enculer",
        r"merde",
        r"putain",
        r"pute",
        r"salope",
        r"salaud",
        r"con",
        r"conne",
        r"couille",
        r"couilles",
        r"bite",
        r"chatte",
        r"foutre",
        r"bordel",
        r"nique",
        r"niquer",
        r"ta mère",
        r"ta mere",
        r"pd",
        r"pédé",
        r"tapette",
        r"taré",
        r"tarée",
        
        # Français - Insultes courantes
        r"débile",
        r"crétin",
        r"abruti",
        r"imbécile",
        r"idiot",
        r"nul",
        r"nulle",
        r"minable",
        r"raclure",
        r"ordure",
        r"pourriture",
        r"casse-toi",
        r"va te faire",
        r"ferme ta gueule",
        r"ta gueule",
    ]

    pattern = re.compile(r"\b(" + r"|".join(profanities) + r")\b", flags=re.IGNORECASE)
    match = pattern.search(texte or "")

    if match:
        word = match.group(1)
        return {
            'accepte': False,
            'score': 1.0,
            'categories': [{'nom': 'profanity', 'nom_fr': 'Vulgarité / Insulte', 'score': 1.0}],
            'details': {'matched': word},
            'message': 'Contenu inapproprié détecté (profanité)'
        }

    return {
        'accepte': True,
        'score': 0.0,
        'categories': [],
        'details': {},
        'message': None
    }


def verifier_contenu(texte: str) -> Dict[str, Any]:
    """
    Wrapper unifié pour vérifier du texte. Si AI_MODERATION_ENABLED est True
    la fonction appelle Perspective/OpenAI selon la configuration. Sinon, elle
    utilise une vérification locale basique pour filtrer les insultes évidentes.
    """
    # Si la modération IA est activée, utiliser la fonction existante
    if getattr(settings, 'AI_MODERATION_ENABLED', False):
        try:
            # Utiliser le chemin Perspective présent dans ce module
            return verifier_contenu_perspective(texte)
        except Exception as e:
            # En cas d'erreur inattendue, bloquer par sécurité
            return {
                'accepte': False,
                'score': 1.0,
                'categories': [{'nom': 'error', 'nom_fr': 'Erreur API', 'score': 1.0}],
                'details': {'error': str(e)},
                'message': 'Service de modération temporairement indisponible.'
            }

    # Sinon, utiliser la vérif locale (fallback)
    return _local_profanity_check(texte)


def verifier_contenu_simple(texte: str, seuil: float = 0.7) -> bool:
    """
    Version simplifiée qui retourne juste True/False
    """
    result = verifier_contenu_perspective(texte)
    return result['accepte']


def get_message_refus(categories: list) -> str:
    """
    Génère un message explicatif en cas de refus
    """
    if not categories:
        return "Votre contenu contient des éléments inappropriés."
    
    categories_fr = [cat['nom_fr'] for cat in categories]
    
    if len(categories_fr) == 1:
        return f"Votre contenu a été détecté comme contenant : {categories_fr[0].lower()}."
    else:
        categories_str = ", ".join(categories_fr[:-1]) + f" et {categories_fr[-1]}"
        return f"Votre contenu a été détecté comme contenant : {categories_str.lower()}."


# Fonction de test
def test_moderation():
    """Test de la modération avec différents types de contenus"""
    
    tests = [
        ("Bonjour, j'ai une question sur Django", True, "Normal"),
        ("Comment installer Python sur Windows ?", True, "Question"),
        ("You are stupid and I hate you", False, "Insulte"),
        ("This is complete garbage", False, "Toxique"),
    ]
    
    print("=== Test de Modération IA (Perspective API) ===\n")
    
    for texte, attendu, type_test in tests:
        result = verifier_contenu_perspective(texte)
        status = "✅ ACCEPTÉ" if result['accepte'] else "❌ REFUSÉ"
        match = "✓" if result['accepte'] == attendu else "✗"
        
        print(f"{match} {status} - Score: {result['score']:.3f} - Type: {type_test}")
        print(f"   Texte: {texte}")
        
        if result['categories']:
            cats = ', '.join([c['nom_fr'] for c in result['categories']])
            print(f"   Catégories: {cats}")
        
        print()


if __name__ == "__main__":
    test_moderation()



def verifier_contenu_openai(texte: str) -> Dict[str, Any]:
    """
    Vérifie si le contenu est approprié en utilisant OpenAI Moderation API
    
    Args:
        texte: Le texte à vérifier (post, commentaire, titre, etc.)
    
    Returns:
        Dict contenant:
        - 'accepte': bool - Si le contenu est acceptable
        - 'score': float - Score de toxicité (0-1)
        - 'categories': list - Liste des catégories problématiques détectées
        - 'details': dict - Détails complets de l'analyse
    """
    
    # Vérifier si OpenAI est configuré
    openai_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    if not openai_key:
        # Si pas de clé API, accepter le contenu (mode dégradé)
        return {
            'accepte': True,
            'score': 0.0,
            'categories': [],
            'details': {},
            'message': 'Modération IA désactivée (pas de clé API)'
        }
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_key)
        
        # Appel à l'API de modération
        response = client.moderations.create(input=texte)
        result = response.results[0]
        
        # Extraire les catégories problématiques
        categories_detectees = []
        scores_categories = {}
        
        for category, flagged in result.categories.model_dump().items():
            if flagged:
                categories_detectees.append({
                    'nom': category,
                    'nom_fr': CATEGORIES_FR.get(category, category),
                    'score': getattr(result.category_scores, category, 0.0)
                })
            scores_categories[category] = getattr(result.category_scores, category, 0.0)
        
        # Calculer le score maximum
        max_score = max(scores_categories.values()) if scores_categories else 0.0
        
        return {
            'accepte': not result.flagged,
            'score': max_score,
            'categories': categories_detectees,
            'details': {
                'flagged': result.flagged,
                'scores': scores_categories
            },
            'message': None if result.flagged is False else 'Contenu potentiellement inapproprié détecté'
        }
        
    except ImportError:
        # Bibliothèque OpenAI non installée
        return {
            'accepte': True,
            'score': 0.0,
            'categories': [],
            'details': {},
            'message': 'Bibliothèque OpenAI non installée'
        }
    
    except Exception as e:
        # En cas d'erreur, REFUSER le contenu par sécurité
        print(f"Erreur lors de la modération IA: {str(e)}")
        
        # Si l'API ne fonctionne pas, on BLOQUE par sécurité
        # Vous pouvez changer en True si vous préférez accepter en cas d'erreur
        return {
            'accepte': False,  # ⬅️ BLOQUE si erreur API
            'score': 1.0,
            'categories': [{'nom': 'error', 'nom_fr': 'Erreur API', 'score': 1.0}],
            'details': {'error': str(e)},
            'message': f'⚠️ Service de modération temporairement indisponible. Veuillez réessayer dans quelques instants.'
        }


def verifier_contenu_simple(texte: str, seuil: float = 0.5) -> bool:
    """
    Version simplifiée qui retourne juste True/False
    
    Args:
        texte: Le texte à vérifier
        seuil: Seuil de tolérance (0-1, défaut 0.5)
    
    Returns:
        bool: True si le contenu est acceptable, False sinon
    """
    result = verifier_contenu_openai(texte)
    
    # Si le contenu est flaggé par OpenAI, vérifier le score
    if not result['accepte']:
        return result['score'] < seuil
    
    return True


def get_message_refus(categories: list) -> str:
    """
    Génère un message explicatif en cas de refus
    
    Args:
        categories: Liste des catégories problématiques
    
    Returns:
        str: Message d'erreur en français
    """
    if not categories:
        return "Votre contenu contient des éléments inappropriés."
    
    categories_fr = [cat['nom_fr'] for cat in categories]
    
    if len(categories_fr) == 1:
        return f"Votre contenu a été détecté comme contenant du {categories_fr[0].lower()}."
    else:
        categories_str = ", ".join(categories_fr[:-1]) + f" et {categories_fr[-1]}"
        return f"Votre contenu a été détecté comme contenant: {categories_str.lower()}."


# Fonction de test (pour vérifier que tout fonctionne)
def test_moderation():
    """Test de la modération avec différents types de contenus"""
    
    tests = [
        ("Bonjour, j'ai une question sur Django", True),
        ("Comment installer Python sur Windows ?", True),
        ("Voici mon code pour résoudre ce problème", True),
        # Ajoutez des tests avec du contenu inapproprié si nécessaire
    ]
    
    print("=== Test de Modération IA ===\n")
    
    for texte, attendu in tests:
        result = verifier_contenu_openai(texte)
        status = "✅ ACCEPTÉ" if result['accepte'] else "❌ REFUSÉ"
        
        print(f"{status} - Score: {result['score']:.3f}")
        print(f"Texte: {texte[:50]}...")
        
        if result['categories']:
            print(f"Catégories: {', '.join([c['nom_fr'] for c in result['categories']])}")
        
        print()


if __name__ == "__main__":
    test_moderation()
