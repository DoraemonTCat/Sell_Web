# ===========================================
# Analytics Models — User Behavior Tracking
# Tracks: VIEW, ADD_CART, REMOVE_CART, PURCHASE actions
# Used for: AI recommendations + "potential customer" detection
# Potential customer = user who added to cart but didn't purchase
# ===========================================
from django.db import models
from django.conf import settings


class UserBehavior(models.Model):
    """
    Tracks user interactions with products.
    - VIEW: user viewed product detail page
    - ADD_CART: user added product to cart
    - REMOVE_CART: user removed product from cart
    - PURCHASE: user completed purchase

    Use cases:
    1. AI Recommendations: cosine similarity based on behavior vectors
    2. Potential Customers: users who ADD_CART but never PURCHASE
    """

    ACTION_CHOICES = [
        ('VIEW', 'Viewed product'),
        ('ADD_CART', 'Added to cart'),
        ('REMOVE_CART', 'Removed from cart'),
        ('PURCHASE', 'Purchased'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='behaviors'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='behaviors'
    )
    action = models.CharField(
        max_length=15,
        choices=ACTION_CHOICES
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Extra data: e.g. cart quantity, time spent viewing"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_behaviors'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['product', 'action']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.action} → {self.product.title}"
