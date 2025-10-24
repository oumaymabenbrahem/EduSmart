from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings

from .models import Category, Topic, Post, Comment, Report
from .forms import TopicForm, PostForm, CommentForm, ReportForm, SearchForm
from .ai_moderation import verifier_contenu, get_message_refus


def forum_index(request):
    """Page d'accueil du forum avec liste des catégories"""
    categories = Category.objects.filter(is_active=True).annotate(
        topics_count=Count('topics', filter=Q(topics__is_active=True)),
        posts_count=Count('topics__posts', filter=Q(topics__is_active=True, topics__posts__is_active=True))
    )
    
    # Derniers sujets actifs
    recent_topics = Topic.objects.filter(is_active=True).select_related('author', 'category').annotate(
        posts_count=Count('posts', filter=Q(posts__is_active=True))
    ).order_by('-updated_at')[:5]
    
    # Statistiques
    total_topics = Topic.objects.filter(is_active=True).count()
    total_posts = Post.objects.filter(is_active=True).count()
    
    context = {
        'categories': categories,
        'recent_topics': recent_topics,
        'total_topics': total_topics,
        'total_posts': total_posts,
    }
    return render(request, 'forum/index.html', context)


def category_detail(request, slug):
    """Liste des sujets dans une catégorie"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    topics_list = Topic.objects.filter(
        category=category,
        is_active=True
    ).select_related('author').annotate(
        posts_count=Count('posts', filter=Q(posts__is_active=True))
    ).order_by('-status', '-updated_at')
    
    # Pagination
    paginator = Paginator(topics_list, 15)
    page_number = request.GET.get('page')
    topics = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'topics': topics,
    }
    return render(request, 'forum/category_detail.html', context)


def topic_detail(request, category_slug, topic_slug):
    """Détail d'un sujet avec ses réponses"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    topic = get_object_or_404(Topic, slug=topic_slug, category=category, is_active=True)
    
    # Incrémenter les vues
    topic.increment_views()
    
    # Récupérer tous les posts avec leurs commentaires
    posts_list = topic.posts.filter(is_active=True).select_related('author').prefetch_related(
        'comments__author',
        'likes'
    ).order_by('created_at')
    
    # Pagination des posts
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    # Formulaire de réponse
    post_form = PostForm()
    
    # === PRÉDICTION DE POPULARITÉ ===
    try:
        from .ai_popularity_predictor import get_predictor
        predictor = get_predictor()
        
        # Analyser la performance du topic
        analysis = predictor.analyze_topic_performance(topic.id)
        
        if 'error' not in analysis:
            # Calculer le score de popularité
            actual_views = analysis['actual_views']
            predicted_views = max(1, analysis['predicted_views'])
            
            # Score basé sur les vues réelles
            score = min(100, (actual_views / 10) + (topic.get_posts_count() * 5))
            
            # Déterminer si c'est trending (surperformance)
            is_trending = actual_views > predicted_views * 1.5
            
            topic.popularity_data = {
                'score': round(score, 1),
                'is_trending': is_trending,
                'predicted_views': predicted_views,
                'actual_views': actual_views,
                'performance': analysis.get('performance', '')
            }
        else:
            topic.popularity_data = None
    except Exception as e:
        print(f"Erreur lors du calcul de popularité: {e}")
        topic.popularity_data = None
    
    # Traiter la soumission d'une réponse
    if request.method == 'POST' and request.user.is_authenticated:
        if 'post_content' in request.POST or request.POST.get('content'):
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                # === MODÉRATION (IA ou fallback local) ===
                contenu = post_form.cleaned_data['content']
                moderation_result = verifier_contenu(contenu)

                if not moderation_result['accepte'] and getattr(settings, 'AI_AUTO_BLOCK', True):
                    message_erreur = get_message_refus(moderation_result.get('categories', []))
                    messages.error(request, f"⚠️ {message_erreur}")
                    messages.warning(request, "Veuillez reformuler votre réponse.")

                    context = {
                        'topic': topic,
                        'category': category,
                        'posts': posts,
                        'post_form': post_form,
                    }
                    return render(request, 'forum/topic_detail.html', context)
                
                # === CRÉATION DU POST ===
                post = post_form.save(commit=False)
                post.topic = topic
                post.author = request.user
                post.save()
                messages.success(request, '✅ Votre réponse a été publiée avec succès!')
                return redirect('forum:topic_detail', category_slug=category.slug, topic_slug=topic.slug)
    
    context = {
        'topic': topic,
        'category': category,
        'posts': posts,
        'post_form': post_form,
    }
    return render(request, 'forum/topic_detail.html', context)


@login_required
def topic_create(request, category_slug):
    """Créer un nouveau sujet"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            # === MODÉRATION (IA ou fallback local) ===
            texte_complet = f"{form.cleaned_data['title']}\n{form.cleaned_data['content']}"
            moderation_result = verifier_contenu(texte_complet)

            if not moderation_result['accepte'] and getattr(settings, 'AI_AUTO_BLOCK', True):
                # Contenu inapproprié détecté
                message_erreur = get_message_refus(moderation_result.get('categories', []))
                messages.error(request, f"⚠️ {message_erreur}")
                messages.warning(request, "Notre système de modération a détecté un contenu potentiellement inapproprié. Veuillez reformuler votre message.")

                # Renvoyer le formulaire avec les données
                context = {
                    'form': form,
                    'category': category,
                    'action': 'create',
                    'ai_blocked': True,
                    'ai_score': moderation_result.get('score', 0.0),
                }
                return render(request, 'forum/topic_form.html', context)
            
            # === CRÉATION DU TOPIC ===
            topic = form.save(commit=False)
            topic.author = request.user
            topic.category = category
            topic.save()
            
            # Créer le premier post
            Post.objects.create(
                topic=topic,
                author=request.user,
                content=form.cleaned_data['content']
            )
            
            messages.success(request, '✅ Votre sujet a été créé avec succès!')
            return redirect('forum:topic_detail', category_slug=category.slug, topic_slug=topic.slug)
    else:
        form = TopicForm()
    
    context = {
        'form': form,
        'category': category,
        'action': 'create',
    }
    return render(request, 'forum/topic_form.html', context)


@login_required
def topic_update(request, category_slug, topic_slug):
    """Modifier un sujet (seulement par l'auteur ou admin)"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    topic = get_object_or_404(Topic, slug=topic_slug, category=category)
    
    # Vérifier les permissions
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, 'Vous n\'avez pas la permission de modifier ce sujet.')
        return redirect('forum:topic_detail', category_slug=category.slug, topic_slug=topic.slug)
    
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            topic = form.save()
            # Mettre à jour le premier post
            if topic.first_post:
                topic.first_post.content = form.cleaned_data['content']
                topic.first_post.save()
            messages.success(request, 'Le sujet a été modifié avec succès!')
            return redirect('forum:topic_detail', category_slug=category.slug, topic_slug=topic.slug)
    else:
        initial_data = {'content': topic.first_post.content if topic.first_post else ''}
        form = TopicForm(instance=topic, initial=initial_data)
    
    context = {
        'form': form,
        'topic': topic,
        'category': category,
        'action': 'edit',
    }
    return render(request, 'forum/topic_form.html', context)


@login_required
def topic_delete(request, category_slug, topic_slug):
    """Supprimer un sujet (seulement par l'auteur ou admin)"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    topic = get_object_or_404(Topic, slug=topic_slug, category=category)
    
    # Vérifier les permissions
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, 'Vous n\'avez pas la permission de supprimer ce sujet.')
        return redirect('forum:topic_detail', category_slug=category.slug, topic_slug=topic.slug)
    
    if request.method == 'POST':
        topic.is_active = False
        topic.save()
        messages.success(request, 'Le sujet a été supprimé avec succès!')
        return redirect('forum:category_detail', slug=category.slug)
    
    return render(request, 'forum/topic_confirm_delete.html', {'topic': topic, 'category': category})


@login_required
def post_edit(request, pk):
    """Modifier un post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Vérifier les permissions
    if request.user != post.author and not request.user.is_staff:
        messages.error(request, 'Vous n\'avez pas la permission de modifier ce post.')
        return redirect('forum:topic_detail', category_slug=post.topic.category.slug, topic_slug=post.topic.slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre réponse a été modifiée!')
            return redirect('forum:topic_detail', category_slug=post.topic.category.slug, topic_slug=post.topic.slug)
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'forum/post_edit.html', context)


@login_required
def post_delete(request, pk):
    """Supprimer un post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Vérifier les permissions
    if request.user != post.author and not request.user.is_staff:
        messages.error(request, 'Vous n\'avez pas la permission de supprimer ce post.')
        return redirect('forum:topic_detail', category_slug=post.topic.category.slug, topic_slug=post.topic.slug)
    
    category_slug = post.topic.category.slug
    topic_slug = post.topic.slug
    post.is_active = False
    post.save()
    messages.success(request, 'La réponse a été supprimée!')
    return redirect('forum:topic_detail', category_slug=category_slug, topic_slug=topic_slug)


@login_required
def post_like(request, pk):
    """Liker/Unliker un post (AJAX)"""
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=pk)
        
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'likes_count': post.likes_count
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def comment_create(request, post_pk):
    """Ajouter un commentaire à un post (AJAX)"""
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_pk)
        form = CommentForm(request.POST)
        
        if form.is_valid():
            # === MODÉRATION (IA ou fallback local) ===
            contenu = form.cleaned_data['content']
            moderation_result = verifier_contenu(contenu)

            if not moderation_result['accepte'] and getattr(settings, 'AI_AUTO_BLOCK', True):
                message_erreur = get_message_refus(moderation_result.get('categories', []))
                return JsonResponse({
                    'success': False,
                    'error': 'ai_blocked',
                    'message': message_erreur
                }, status=400)
            
            # === CRÉATION DU COMMENTAIRE ===
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'author': comment.author.username,
                    'author_picture': comment.author.profile_picture.url if comment.author.profile_picture else None,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
                }
            })
        
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def comment_delete(request, pk):
    """Supprimer un commentaire"""
    comment = get_object_or_404(Comment, pk=pk)
    
    # Vérifier les permissions
    if request.user != comment.author and not request.user.is_staff:
        messages.error(request, 'Vous n\'avez pas la permission de supprimer ce commentaire.')
        return redirect('forum:topic_detail', category_slug=comment.post.topic.category.slug, topic_slug=comment.post.topic.slug)
    
    category_slug = comment.post.topic.category.slug
    topic_slug = comment.post.topic.slug
    comment.is_active = False
    comment.save()
    messages.success(request, 'Le commentaire a été supprimé!')
    return redirect('forum:topic_detail', category_slug=category_slug, topic_slug=topic_slug)


@login_required
def mark_solution(request, post_pk):
    """Marquer un post comme solution (seulement l'auteur du topic ou admin)"""
    post = get_object_or_404(Post, pk=post_pk)
    topic = post.topic
    
    # Vérifier les permissions
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, 'Vous n\'avez pas la permission de marquer une solution.')
        return redirect('forum:topic_detail', category_slug=topic.category.slug, topic_slug=topic.slug)
    
    # Retirer la marque solution des autres posts
    topic.posts.update(is_solution=False)
    
    # Marquer ce post comme solution
    post.is_solution = True
    post.save()
    
    messages.success(request, 'Cette réponse a été marquée comme solution!')
    return redirect('forum:topic_detail', category_slug=topic.category.slug, topic_slug=topic.slug)


def search(request):
    """Recherche dans le forum"""
    form = SearchForm(request.GET)
    topics = Topic.objects.none()
    query = ''
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        category_id = form.cleaned_data.get('category', '')
        
        topics = Topic.objects.filter(is_active=True).select_related('author', 'category').annotate(
            posts_count=Count('posts', filter=Q(posts__is_active=True))
        )
        
        if query:
            topics = topics.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__icontains=query)
            )
        
        if category_id:
            topics = topics.filter(category_id=category_id)
        
        topics = topics.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(topics, 15)
    page_number = request.GET.get('page')
    topics_page = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'topics': topics_page,
        'query': query,
    }
    return render(request, 'forum/search.html', context)


@login_required
def report_content(request):
    """Signaler un contenu inapproprié"""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_type = request.POST.get('content_type')
            report.content_id = request.POST.get('content_id')
            report.save()
            
            # Vérifier le nombre de signalements pour ce contenu
            content_reports_count = Report.objects.filter(
                content_type=report.content_type,
                content_id=report.content_id,
                status='pending'
            ).count()
            
            # BLOCAGE AUTOMATIQUE : Seuil de 3 signalements
            if content_reports_count >= 3:
                if report.content_type == 'topic':
                    try:
                        topic = Topic.objects.get(id=report.content_id)
                        topic.is_active = False
                        topic.save()
                        messages.warning(request, 'Ce contenu a été automatiquement masqué suite à plusieurs signalements.')
                    except Topic.DoesNotExist:
                        pass
                elif report.content_type == 'post':
                    try:
                        post = Post.objects.get(id=report.content_id)
                        post.is_active = False
                        post.save()
                        messages.warning(request, 'Ce contenu a été automatiquement masqué suite à plusieurs signalements.')
                    except Post.DoesNotExist:
                        pass
                elif report.content_type == 'comment':
                    try:
                        comment = Comment.objects.get(id=report.content_id)
                        comment.is_active = False
                        comment.save()
                        messages.warning(request, 'Ce contenu a été automatiquement masqué suite à plusieurs signalements.')
                    except Comment.DoesNotExist:
                        pass
            else:
                messages.success(request, 'Votre signalement a été enregistré. Merci!')
            
            return redirect(request.POST.get('return_url', 'forum:index'))
    
    return redirect('forum:index')


@login_required
def my_topics(request):
    """Liste des sujets créés par l'utilisateur"""
    topics_list = Topic.objects.filter(
        author=request.user,
        is_active=True
    ).select_related('category').annotate(
        posts_count=Count('posts', filter=Q(posts__is_active=True))
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(topics_list, 15)
    page_number = request.GET.get('page')
    topics = paginator.get_page(page_number)
    
    context = {
        'topics': topics,
    }
    return render(request, 'forum/my_topics.html', context)


@login_required
def my_posts(request):
    """Liste des posts/réponses de l'utilisateur"""
    posts_list = Post.objects.filter(
        author=request.user,
        is_active=True
    ).select_related('topic', 'topic__category').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts_list, 20)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'posts': posts,
    }
    return render(request, 'forum/my_posts.html', context)


@login_required
def reports_list(request):
    """Liste des signalements (pour les admins)"""
    if not request.user.is_staff:
        messages.error(request, 'Vous n\'avez pas accès à cette page.')
        return redirect('forum:index')
    
    # Filtrer par statut
    status_filter = request.GET.get('status', 'pending')
    reports = Report.objects.filter(status=status_filter).select_related('reporter').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    reports_page = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'pending': Report.objects.filter(status='pending').count(),
        'reviewed': Report.objects.filter(status='reviewed').count(),
        'resolved': Report.objects.filter(status='resolved').count(),
        'rejected': Report.objects.filter(status='rejected').count(),
    }
    
    context = {
        'reports': reports_page,
        'status_filter': status_filter,
        'stats': stats,
    }
    return render(request, 'forum/reports_list.html', context)
