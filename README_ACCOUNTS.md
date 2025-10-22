# Système de Gestion d'Utilisateurs EduSmart

## 📋 Vue d'ensemble

Ce système de gestion d'utilisateurs complet a été développé pour EduSmart avec un design moderne et une architecture bien structurée. Il inclut toutes les fonctionnalités essentielles pour la gestion des comptes utilisateurs.

## 🚀 Fonctionnalités

### ✅ Authentification
- **Inscription** avec validation en temps réel
- **Connexion** avec email ou nom d'utilisateur
- **Déconnexion** sécurisée
- **Changement de mot de passe**

### 👤 Gestion des Profils
- **Profil utilisateur complet** avec photo
- **Édition du profil** avec prévisualisation d'image
- **Types d'utilisateurs** : Étudiant, Enseignant, Administrateur
- **Informations personnelles** étendues

### 🎨 Interface Utilisateur
- **Design moderne** avec Bootstrap 5
- **Interface responsive** pour tous les appareils
- **Animations fluides** et transitions
- **Thème cohérent** avec le template existant

### 🔧 Administration
- **Interface d'administration** Django personnalisée
- **Gestion des utilisateurs** en masse
- **Vérification des comptes**
- **Statistiques et rapports**

## 📁 Structure du Projet

```
accounts/
├── models.py          # Modèle User personnalisé
├── forms.py           # Formulaires d'authentification
├── views.py           # Vues pour toutes les fonctionnalités
├── urls.py            # Configuration des URLs
├── admin.py           # Interface d'administration
└── templates/accounts/
    ├── base.html      # Template de base
    ├── login.html     # Page de connexion
    ├── register.html  # Page d'inscription
    ├── dashboard.html # Tableau de bord
    ├── profile.html   # Profil utilisateur
    ├── edit_profile.html
    ├── change_password.html
    ├── users_list.html
    └── delete_account.html
```

## 🛠️ Installation et Configuration

### 1. Prérequis
```bash
pip install Django Pillow
```

### 2. Configuration de la Base de Données
```bash
# Réinitialiser la base de données (si nécessaire)
python reset_db.py

# Créer le superutilisateur et des utilisateurs de test
python create_superuser.py
```

### 3. Lancement du Serveur
```bash
python manage.py runserver
```

## 🔗 URLs Disponibles

| URL | Description | Accès |
|-----|-------------|-------|
| `/accounts/register/` | Inscription | Public |
| `/accounts/login/` | Connexion | Public |
| `/accounts/logout/` | Déconnexion | Connecté |
| `/accounts/dashboard/` | Tableau de bord | Connecté |
| `/accounts/profile/` | Mon profil | Connecté |
| `/accounts/profile/edit/` | Modifier le profil | Connecté |
| `/accounts/password/change/` | Changer le mot de passe | Connecté |
| `/accounts/users/` | Liste des utilisateurs | Connecté |
| `/accounts/delete-account/` | Supprimer le compte | Connecté |

## 👥 Comptes de Test

### Administrateur
- **Username:** admin
- **Password:** admin123
- **Email:** admin@edusmart.com

### Étudiant
- **Username:** student1
- **Password:** student123
- **Email:** student1@edusmart.com

### Enseignant
- **Username:** teacher1
- **Password:** teacher123
- **Email:** teacher1@edusmart.com

## 🎨 Personnalisation du Design

### Couleurs Principales
- **Primaire:** `#5fcf80` (Vert EduSmart)
- **Secondaire:** `#667eea` (Bleu dégradé)
- **Accent:** `#14a085` (Vert foncé)

### Classes CSS Personnalisées
- `.user-type-badge` - Badge pour le type d'utilisateur
- `.stats-card` - Cartes de statistiques
- `.profile-card` - Carte de profil
- `.auth-card` - Cartes d'authentification

## 🔒 Sécurité

### Fonctionnalités de Sécurité
- **Validation des mots de passe** Django intégrée
- **Protection CSRF** sur tous les formulaires
- **Vérification des emails** uniques
- **Validation des données** côté serveur et client
- **Redimensionnement automatique** des images

### Permissions
- **Accès restreint** aux pages connectées
- **Validation des propriétaires** pour l'édition
- **Protection contre** la suppression accidentelle

## 📱 Responsive Design

Le système est entièrement responsive avec :
- **Breakpoints Bootstrap 5**
- **Navigation adaptative**
- **Cartes flexibles**
- **Formulaires optimisés mobile**

## 🔧 Fonctionnalités Avancées

### AJAX
- **Vérification en temps réel** des noms d'utilisateur
- **Validation des emails** en direct
- **Recherche dynamique** dans la liste des utilisateurs

### Animations
- **Transitions fluides** entre les pages
- **Animations d'entrée** pour les éléments
- **Feedback visuel** pour les interactions

### Gestion des Fichiers
- **Upload d'images** avec prévisualisation
- **Redimensionnement automatique**
- **Validation des formats** d'image

## 🚀 Déploiement

### Variables d'Environnement Recommandées
```python
# settings.py
DEBUG = False  # En production
ALLOWED_HOSTS = ['votre-domaine.com']
SECRET_KEY = 'votre-clé-secrète-sécurisée'
```

### Fichiers Statiques
```bash
python manage.py collectstatic
```

## 📞 Support

Pour toute question ou problème :
1. Vérifiez les logs Django
2. Consultez la documentation Django
3. Testez avec les comptes de démonstration

## 🎯 Prochaines Étapes

### Améliorations Possibles
- **Authentification à deux facteurs**
- **Connexion via réseaux sociaux**
- **Système de notifications**
- **API REST** pour mobile
- **Gestion des rôles** avancée

---

**Développé avec ❤️ pour EduSmart**
