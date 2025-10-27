"""
Context processors pour les réclamations
"""
from .views import get_teacher_reclamations_stats
from .models import ReponseAdministrateur

def reclamations_context(request):
    """
    Ajoute les informations de réclamations au contexte global
    """
    context = {}
    
    if request.user.is_authenticated:
        # Statistiques pour les enseignants
        if request.user.user_type == 'teacher' or request.user.is_staff:
            teacher_stats = get_teacher_reclamations_stats(request.user)
            if teacher_stats:
                context['teacher_reclamations_stats'] = teacher_stats
        
        # Compteur de réponses non lues pour tous les utilisateurs
        reponses_non_lues = ReponseAdministrateur.objects.filter(
            reclamation__utilisateur=request.user,
            statut='publiee',
            lu_par_utilisateur=False
        ).count()
        
        context['user_unread_responses'] = reponses_non_lues
    
    return context
