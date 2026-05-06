# ===========================================
# Analytics Admin Configuration
# ===========================================
from django.contrib import admin
from .models import UserBehavior


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'product', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'product__title')
    readonly_fields = ('created_at',)
