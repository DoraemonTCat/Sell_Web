# ===========================================
# Order Admin Configuration
# ===========================================
from django.contrib import admin
from .models import SaleOrder, OrderItem, Payment, DeliverySlip


class OrderItemInline(admin.TabularInline):
    """Show order items inline within the order admin page."""
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


class PaymentInline(admin.StackedInline):
    """Show payment info inline within the order admin page."""
    model = Payment
    extra = 0


class DeliverySlipInline(admin.StackedInline):
    """Show delivery slip inline within the order admin page."""
    model = DeliverySlip
    extra = 0
    readonly_fields = ('slip_number', 'stock_deducted')


@admin.register(SaleOrder)
class SaleOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'buyer', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'buyer__username', 'buyer__email')
    readonly_fields = ('order_number', 'total_amount')
    inlines = [OrderItemInline, PaymentInline, DeliverySlipInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount_received', 'status', 'payment_method', 'paid_at')
    list_filter = ('status', 'payment_method')


@admin.register(DeliverySlip)
class DeliverySlipAdmin(admin.ModelAdmin):
    list_display = ('slip_number', 'order', 'tracking_number', 'stock_deducted', 'printed_at')
    list_filter = ('stock_deducted',)
    readonly_fields = ('slip_number',)
