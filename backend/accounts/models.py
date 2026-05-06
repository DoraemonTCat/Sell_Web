# ===========================================
# User Model — Custom user extending AbstractUser
# Adds: address, google_id, avatar_url
# Every user can be both buyer and seller
# ===========================================
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for Sell_Web.
    - Extends Django's AbstractUser (username, email, password built-in)
    - Adds address for shipping/billing
    - Stores Google OAuth ID for social login
    - Every user can act as both buyer and seller
    """

    # Google OAuth fields
    google_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Google OAuth subject ID"
    )
    avatar_url = models.URLField(
        blank=True,
        null=True,
        help_text="Profile picture URL from Google"
    )

    # Shipping/billing address
    address = models.TextField(
        blank=True,
        default='',
        help_text="User's shipping/billing address"
    )

    # Role: buyer or seller
    ROLE_CHOICES = [
        ('buyer', 'ผู้ซื้อ'),
        ('seller', 'ผู้ขาย'),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='buyer',
        help_text="User role: buyer or seller"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.email})"
