# ===========================================
# User Admin Configuration
# Registers custom User model in Django admin panel
# ===========================================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin config for custom User model with extra fields."""
    list_display = ('username', 'email', 'google_id', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'google_id')

    # Add custom fields to the admin form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('google_id', 'avatar_url', 'address'),
        }),
    )
