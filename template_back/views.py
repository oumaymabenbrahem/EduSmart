from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def dashboard(request):
    # Statistiques pour le dashboard admin
    context = {
        'total_users': User.objects.count(),
        'students_count': User.objects.filter(user_type='student').count(),
        'teachers_count': User.objects.filter(user_type='teacher').count(),
        'admins_count': User.objects.filter(user_type='admin').count(),
        'verified_users': User.objects.filter(is_verified=True).count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
        'current_user': request.user,
    }
    return render(request, 'dashboard.html', context)
