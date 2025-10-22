from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_verified', 'is_active', 'created_at', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('user_type', 'phone_number', 'date_of_birth', 'profile_picture', 'bio')
        }),
        ('Adresse', {
            'fields': ('address', 'city', 'country')
        }),
        ('Statut', {
            'fields': ('is_verified',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('user_type', 'email', 'first_name', 'last_name', 'phone_number')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    actions = ['verify_users', 'unverify_users']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} utilisateur(s) vérifié(s) avec succès.')
    verify_users.short_description = "Vérifier les utilisateurs sélectionnés"
    
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} utilisateur(s) non vérifié(s).')
    unverify_users.short_description = "Retirer la vérification des utilisateurs sélectionnés"
