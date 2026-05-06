# ===========================================
# Product Admin Configuration
# ===========================================
from django.contrib import admin
from .models import Product, StockLog


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'unit_price', 'quantity', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'seller__username')
    list_editable = ('is_active',)


@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_change', 'reason', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('product__title',)
    readonly_fields = ('created_at',)
