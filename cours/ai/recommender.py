import os
import sys
import django
import pickle
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Avg

# 🔹 Ajouter la racine du projet au PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

# 🔹 Définir les settings Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EduSmart.settings")

# 🔹 Initialiser Django
django.setup()

# 🔹 Maintenant on peut importer les modèles Django
from cours.models import Course, CourseEnrollment, CourseReview
from django.conf import settings

# Chemin fixe pour le pickle
PICKLE_FILE = os.path.join(settings.BASE_DIR, 'cours', 'ai', 'tfidf_model.pkl')


def normalize_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

def load_courses_from_db():
    """
    Charger uniquement les cours actifs et publiés pour le modèle.
    """
    courses = Course.objects.filter(is_active=True, status='published')
    df = []
    seen_titles = set()
    for c in courses:
        title_norm = normalize_text(c.title)
        if title_norm in seen_titles:
            continue
        seen_titles.add(title_norm)
        avg_rating = CourseReview.objects.filter(course=c).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0
        df.append({
            "id": c.id,
            "title": c.title,
            "description": c.description or "",
            "average_rating": avg_rating,
        })
    return df



def train_model():
    print("🤖 Entraînement du modèle sur les cours actifs de la base...")
    df = load_courses_from_db()
    descriptions = [normalize_text(c['description']) for c in df]

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(descriptions)

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    os.makedirs(os.path.dirname(PICKLE_FILE), exist_ok=True)
    with open(PICKLE_FILE, 'wb') as f:
        pickle.dump({'tfidf': tfidf, 'cosine_sim': cosine_sim, 'courses': df}, f)

    print(f"✅ Modèle TF-IDF entraîné sur {len(df)} cours")
    return df, tfidf, cosine_sim


def load_model():
    if not os.path.exists(PICKLE_FILE):
        train_model()
    with open(PICKLE_FILE, 'rb') as f:
        data = pickle.load(f)
    return data['courses'], data['cosine_sim']


def recommend_courses(course_title, top_n=5, exclude_ids=None, min_similarity=0.1):
    """
    Recommander des cours similaires, uniquement parmi les cours publiés.
    """
    exclude_ids = exclude_ids or []
    df, cosine_sim = load_model()  # df contient uniquement les cours publiés

    titles = [normalize_text(c['title']) for c in df]
    course_title_norm = normalize_text(course_title)

    if course_title_norm not in titles:
        return []

    idx = titles.index(course_title_norm)
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Garder uniquement les cours différents et publiés
    sim_scores = [
        (i, score * (df[i]['average_rating'] + 1))
        for i, score in sim_scores
        if i != idx and df[i]['id'] not in exclude_ids and score >= min_similarity
    ]
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    top_indices = [i for i, score in sim_scores][:top_n]
    results = [(df[i]['title'], df[i]['average_rating']) for i in top_indices]
    return results


def recommend_for_student(student, top_n=5, min_similarity=0.1):
    """
    Générer les recommandations pour un étudiant en s'assurant que seuls
    les cours publiés sont pris en compte.
    """
    enrollments = CourseEnrollment.objects.filter(student=student)

    if not enrollments:
        return []

    enrolled_course_ids = [e.course.id for e in enrollments if e.course.status == 'published']
    all_recs = []

    for e in enrollments:
        if e.course.status != 'published':
            continue
        recs = recommend_courses(
            e.course.title,
            top_n=top_n,
            exclude_ids=enrolled_course_ids,
            min_similarity=min_similarity
        )
        all_recs.extend(recs)

    # Supprimer doublons
    seen = set()
    unique_recs = []
    for title, rating in all_recs:
        if title not in seen:
            seen.add(title)
            unique_recs.append((title, rating))

    return unique_recs[:top_n]
