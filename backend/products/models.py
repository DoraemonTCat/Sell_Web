# ===========================================
# Product Models
# Product: seller's inventory item with image, price, quantity
# StockLog: audit trail for every stock change (add/deduct)
# ===========================================
from django.db import models
from django.conf import settings


class Product(models.Model):
    """
    Product listed by a seller.
    - seller: FK to User who created this product
    - image: product photo uploaded by seller
    - quantity: current stock count (updated via StockLog)
    - is_active: soft delete flag (hide without deleting)
    """

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        help_text="User who sells this product"
    )

    # Product info (required by spec: image, title, description, unit_price, quantity)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per unit in THB"
    )
    quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current stock quantity"
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text="Product photo"
    )

    # Soft delete — hide product without losing data
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — ฿{self.unit_price}"


class StockLog(models.Model):
    """
    Audit log for every stock change.
    - Positive quantity_change = stock added (seller restocks)
    - Negative quantity_change = stock deducted (order shipped)
    - Tracks reason for accountability
    """

    REASON_CHOICES = [
        ('RESTOCK', 'Seller restocked'),
        ('ORDER_SHIPPED', 'Order shipped — stock deducted'),
        ('ADJUSTMENT', 'Manual adjustment'),
        ('RETURN', 'Customer return'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_logs'
    )
    quantity_change = models.IntegerField(
        help_text="Positive = added, Negative = deducted"
    )
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default='RESTOCK'
    )
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_logs'
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.quantity_change > 0 else ''
        return f"{self.product.title}: {sign}{self.quantity_change} ({self.reason})"
