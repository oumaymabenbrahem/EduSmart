from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Subject, Course, CourseEnrollment, CourseReview, CourseModule, CourseResource
from .forms import CourseForm, SimpleCourseForm, CourseModuleForm, CourseResourceForm


@login_required
def admin_course_list(request):
    """Vue administrative de la liste des cours"""
    if not request.user.is_staff and request.user.user_type != 'teacher':
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('template_back:dashboard')

    # Get all courses with related data and annotations
    courses = Course.objects.select_related('instructor', 'subject')\
        .annotate(
            total_enrollments=Count('enrolled_students'),
            average_rating=Avg('ratings__rating')
        ).prefetch_related('modules', 'resources')

    # Filtres
    subject_slug = request.GET.get('subject')
    level = request.GET.get('level')
    status = request.GET.get('status')
    search = request.GET.get('search')

    if subject_slug:
        courses = courses.filter(subject__slug=subject_slug)
    if level:
        courses = courses.filter(level=level)
    if status:
        courses = courses.filter(status=status)
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(instructor__username__icontains=search) |
            Q(instructor__first_name__icontains=search) |
            Q(instructor__last_name__icontains=search)
        )

    # Trier par date de création par défaut
    courses = courses.order_by('-created_at')

    # Pagination avec 9 cours par page (3x3 grid)
    paginator = Paginator(courses, 9)
    page = request.GET.get('page')
    courses = paginator.get_page(page)

    # Liste des matières pour le filtre
    subjects = Subject.objects.filter(is_active=True)

    # Calculate additional stats for display
    for course in courses:
        course.duration_hours = sum(module.duration for module in course.modules.all() if module.duration)
        course.resource_count = course.resources.count()

    context = {
        'courses': courses,
        'subjects': subjects,
        'current_subject': subject_slug,
        'current_level': level,
        'current_status': status,
        'search_query': search,
    }

    return render(request, 'cours/admin_course_list.html', context)

def course_list(request):
    """Liste des cours avec filtres"""
    courses = Course.objects.filter(status='published', is_active=True)

    # Filtres
    subject_slug = request.GET.get('subject')
    level = request.GET.get('level')
    search = request.GET.get('search')

    if subject_slug:
        courses = courses.filter(subject__slug=subject_slug)

    if level:
        courses = courses.filter(level=level)

    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(subject__name__icontains=search)
        )

    # Tri
    sort_by = request.GET.get('sort', 'created_at')
    if sort_by == 'views':
        courses = courses.order_by('-total_views')
    elif sort_by == 'enrollments':
        courses = courses.order_by('-total_enrollments')
    elif sort_by == 'rating':
        courses = courses.order_by('-average_rating')
    else:
        courses = courses.order_by('-created_at')

    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques
    subjects = Subject.objects.filter(is_active=True).annotate(
        course_count=Count('courses', filter=Q(courses__status='published', courses__is_active=True))
    )

    context = {
        'page_obj': page_obj,
        'subjects': subjects,
        'current_subject': subject_slug,
        'current_level': level,
        'search_query': search,
        'sort_by': sort_by,
    }

    return render(request, 'cours/course_list.html', context)


def subject_list(request):
    """Liste des matières"""
    subjects = Subject.objects.filter(is_active=True).annotate(
        course_count=Count('courses', filter=Q(courses__status='published', courses__is_active=True))
    ).order_by('name')

    context = {
        'subjects': subjects,
    }

    return render(request, 'cours/subject_list.html', context)


def subject_detail(request, slug):
    """Détail d'une matière"""
    subject = get_object_or_404(Subject, slug=slug, is_active=True)

    courses = Course.objects.filter(
        subject=subject,
        status='published',
        is_active=True
    ).order_by('-created_at')

    context = {
        'subject': subject,
        'courses': courses,
    }

    return render(request, 'cours/subject_detail.html', context)


def course_detail(request, slug):
    """Détail d'un cours"""
    course = get_object_or_404(Course, slug=slug, status='published', is_active=True)

    # Incrémenter les vues
    course.increment_views()

    # Vérifier si l'utilisateur est inscrit
    is_enrolled = False
    enrollment = None
    user_review = None

    if request.user.is_authenticated:
        enrollment = CourseEnrollment.objects.filter(
            student=request.user,
            course=course
        ).first()
        is_enrolled = enrollment is not None

        # Récupérer l'avis de l'utilisateur
        user_review = CourseReview.objects.filter(
            student=request.user,
            course=course
        ).first()

    # Modules du cours
    modules = CourseModule.objects.filter(course=course, is_active=True).order_by('order')

    # Ressources du cours
    resources = CourseResource.objects.filter(course=course, is_active=True).order_by('created_at')

    # Avis récents
    reviews = CourseReview.objects.filter(course=course).order_by('-created_at')[:5]

    # Cours similaires
    similar_courses = Course.objects.filter(
        subject=course.subject,
        status='published',
        is_active=True
    ).exclude(id=course.id).order_by('-total_views')[:4]

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'user_review': user_review,
        'modules': modules,
        'resources': resources,
        'reviews': reviews,
        'similar_courses': similar_courses,
    }

    return render(request, 'cours/course_detail.html', context)


@login_required
def course_enroll(request, slug):
    """Inscription à un cours"""
    course = get_object_or_404(Course, slug=slug, status='published', is_active=True)

    # Vérifier si déjà inscrit
    if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
        messages.warning(request, "Vous êtes déjà inscrit à ce cours.")
        return redirect('cours:course_detail', slug=slug)

    # Créer l'inscription
    CourseEnrollment.objects.create(
        student=request.user,
        course=course,
        status='enrolled'
    )

    # Incrémenter le compteur d'inscriptions
    course.total_enrollments += 1
    course.save(update_fields=['total_enrollments'])

    messages.success(request, f"Vous êtes maintenant inscrit au cours '{course.title}'.")
    return redirect('cours:course_detail', slug=slug)


@login_required
def course_unenroll(request, slug):
    """Désinscription d'un cours"""
    course = get_object_or_404(Course, slug=slug, status='published', is_active=True)

    enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=course
    ).first()

    if not enrollment:
        messages.warning(request, "Vous n'êtes pas inscrit à ce cours.")
        return redirect('cours:course_detail', slug=slug)

    # Supprimer l'inscription
    enrollment.delete()

    # Décrémenter le compteur d'inscriptions
    course.total_enrollments = max(0, course.total_enrollments - 1)
    course.save(update_fields=['total_enrollments'])

    messages.success(request, f"Vous vous êtes désinscrit du cours '{course.title}'.")
    return redirect('cours:course_detail', slug=slug)


@login_required
def course_progress(request, slug):
    """Mettre à jour la progression d'un cours"""
    course = get_object_or_404(Course, slug=slug, status='published', is_active=True)

    enrollment = get_object_or_404(
        CourseEnrollment,
        student=request.user,
        course=course
    )

    if request.method == 'POST':
        progress = request.POST.get('progress')
        if progress and progress.isdigit():
            progress = int(progress)
            if 0 <= progress <= 100:
                enrollment.progress_percentage = progress
                if progress == 100:
                    enrollment.status = 'completed'
                    enrollment.completed_at = timezone.now()
                enrollment.save()
                messages.success(request, "Progression mise à jour.")
            else:
                messages.error(request, "La progression doit être entre 0 et 100.")
        else:
            messages.error(request, "Valeur de progression invalide.")

    return redirect('cours:course_detail', slug=slug)


@login_required
def course_create(request):
    """Créer un nouveau cours (enseignants uniquement)"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Vous n'avez pas la permission de créer un cours.")
        return redirect('cours:course_list')

    if request.method == 'POST':
        form = SimpleCourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            # Valeurs par défaut pour les champs non inclus dans le formulaire simplifié
            course.subject = Subject.objects.filter(is_active=True).first()  # Première matière active par défaut
            course.level = 'beginner'
            course.content = f"Contenu du cours {course.title}"
            course.duration_hours = 1
            course.status = 'published'
            course.save()
            messages.success(request, f"Le cours '{course.title}' a été créé avec succès.")
            return redirect('cours:course_list')
    else:
        form = SimpleCourseForm()

    context = {
        'form': form,
    }

    return render(request, 'cours/course_form.html', context)


@login_required
def course_module_create(request, slug):
    """Créer un module pour un cours (enseignants uniquement)"""
    course = get_object_or_404(Course, slug=slug, instructor=request.user)

    if request.method == 'POST':
        form = CourseModuleForm(request.POST, request.FILES)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, f"Le module '{module.title}' a été ajouté au cours.")
            return redirect('cours:course_detail', slug=slug)
    else:
        form = CourseModuleForm()

    context = {
        'form': form,
        'course': course,
        'action': 'create_module'
    }

    return render(request, 'cours/course_form.html', context)


@login_required
def course_module_edit(request, slug, module_id):
    """Modifier un module de cours (enseignants uniquement)"""
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    module = get_object_or_404(CourseModule, id=module_id, course=course)

    if request.method == 'POST':
        form = CourseModuleForm(request.POST, request.FILES, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le module '{module.title}' a été modifié.")
            return redirect('cours:course_detail', slug=slug)
    else:
        form = CourseModuleForm(instance=module)

    context = {
        'form': form,
        'course': course,
        'module': module,
        'action': 'edit_module'
    }

    return render(request, 'cours/course_form.html', context)


@login_required
def course_module_delete(request, slug, module_id):
    """Supprimer un module de cours (enseignants uniquement)"""
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    module = get_object_or_404(CourseModule, id=module_id, course=course)

    if request.method == 'POST':
        module_title = module.title
        module.delete()
        messages.success(request, f"Le module '{module_title}' a été supprimé.")
        return redirect('cours:course_detail', slug=slug)

    context = {
        'course': course,
        'module': module,
        'action': 'delete_module'
    }

    return render(request, 'cours/course_form.html', context)


@login_required
def course_resource_create(request, slug):
    """Ajouter une ressource à un cours (enseignants uniquement)"""
    course = get_object_or_404(Course, slug=slug, instructor=request.user)

    if request.method == 'POST':
        form = CourseResourceForm(request.POST, request.FILES, course=course)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.course = course
            resource.save()
            messages.success(request, f"La ressource '{resource.title}' a été ajoutée au cours.")
            return redirect('cours:course_detail', slug=slug)
    else:
        form = CourseResourceForm(course=course)

    context = {
        'form': form,
        'course': course,
        'action': 'create_resource'
    }

    return render(request, 'cours/course_form.html', context)


@login_required
def course_resource_edit(request, slug, resource_id):
    """Modifier une ressource de cours (enseignants uniquement)"""
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    resource = get_object_or_404(CourseResource, id=resource_id, course=course)

    if request.method == 'POST':
        form = CourseResourceForm(request.POST, request.FILES, course=course, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f"La ressource '{resource.title}' a été modifiée.")
            return redirect('cours:course_detail', slug=slug)
    else:
        form = CourseResourceForm(course=course, instance=resource)

    context = {
        'form': form,
        'course': course,
        'resource': resource,
        'action': 'edit_resource'
    }

    return render(request, 'cours/course_form.html', context)


@login_required
def course_resource_delete(request, slug, resource_id):
    """Supprimer une ressource de cours (enseignants uniquement)"""
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    resource = get_object_or_404(CourseResource, id=resource_id, course=course)

    if request.method == 'POST':
        resource_title = resource.title
        resource.delete()
        messages.success(request, f"La ressource '{resource_title}' a été supprimée.")
        return redirect('cours:course_detail', slug=slug)

    context = {
        'course': course,
        'resource': resource,
        'action': 'delete_resource'
    }

    return render(request, 'cours/course_form.html', context)


@login_required
def course_review(request, slug):
    """Ajouter/modifier un avis sur un cours"""
    course = get_object_or_404(Course, slug=slug, status='published', is_active=True)

    # Vérifier que l'utilisateur est inscrit
    if not CourseEnrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, "Vous devez être inscrit au cours pour donner un avis.")
        return redirect('cours:course_detail', slug=slug)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        if rating and rating.isdigit():
            rating = int(rating)
            if 1 <= rating <= 5:
                review, created = CourseReview.objects.update_or_create(
                    student=request.user,
                    course=course,
                    defaults={
                        'rating': rating,
                        'comment': comment
                    }
                )

                # Recalculer la note moyenne
                avg_rating = CourseReview.objects.filter(course=course).aggregate(
                    avg_rating=Avg('rating')
                )['avg_rating'] or 0.0

                course.average_rating = round(avg_rating, 1)
                course.save(update_fields=['average_rating'])

                messages.success(request, "Votre avis a été enregistré.")
            else:
                messages.error(request, "La note doit être entre 1 et 5.")
        else:
            messages.error(request, "Veuillez sélectionner une note.")

    return redirect('cours:course_detail', slug=slug)


# API Views pour AJAX (optionnel)

@login_required
def api_enroll_course(request, course_id):
    """API pour s'inscrire à un cours via AJAX"""
    try:
        course = get_object_or_404(Course, id=course_id, status='published', is_active=True)

        if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
            return JsonResponse({'success': False, 'message': 'Déjà inscrit'})

        CourseEnrollment.objects.create(
            student=request.user,
            course=course,
            status='enrolled'
        )

        course.total_enrollments += 1
        course.save(update_fields=['total_enrollments'])

        return JsonResponse({'success': True, 'message': 'Inscription réussie'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def api_update_progress(request, enrollment_id):
    """API pour mettre à jour la progression via AJAX"""
    try:
        enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id, student=request.user)

        progress = request.POST.get('progress')
        if progress and progress.isdigit():
            progress = int(progress)
            if 0 <= progress <= 100:
                enrollment.progress_percentage = progress
                if progress == 100:
                    enrollment.status = 'completed'
                    from django.utils import timezone
                    enrollment.completed_at = timezone.now()
                enrollment.save()

                return JsonResponse({'success': True, 'message': 'Progression mise à jour'})
            else:
                return JsonResponse({'success': False, 'message': 'Progression invalide'})
        else:
            return JsonResponse({'success': False, 'message': 'Données invalides'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def course_delete(request, slug):
    """Supprimer un cours (admin et enseignant propriétaire uniquement)"""
    course = get_object_or_404(Course, slug=slug)

    # Vérifier les permissions
    if not request.user.is_staff and (request.user.user_type != 'teacher' or course.instructor != request.user):
        messages.error(request, "Vous n'avez pas la permission de supprimer ce cours.")
        return redirect('cours:admin_course_list')

    if request.method == 'POST':
        # Supprimer les inscriptions
        CourseEnrollment.objects.filter(course=course).delete()
        
        # Supprimer les avis
        CourseReview.objects.filter(course=course).delete()
        
        # Supprimer les ressources
        CourseResource.objects.filter(course=course).delete()
        
        # Supprimer les modules
        CourseModule.objects.filter(course=course).delete()
        
        # Supprimer le cours
        course.delete()
        
        messages.success(request, f"Le cours '{course.title}' a été supprimé avec succès.")
        return redirect('cours:admin_course_list')

    return redirect('cours:admin_course_list')
