# ===========================================
# Order Models — Full order lifecycle
# SaleOrder: buyer's order (PENDING → PAID → SHIPPED → COMPLETED)
# OrderItem: individual product in an order
# Payment: payment slip upload with verification status
# DeliverySlip: printable slip for shipping + stock deduction
# ===========================================
import uuid
from django.db import models
from django.conf import settings


class SaleOrder(models.Model):
    """
    Buyer's purchase order containing multiple products.
    Status lifecycle: PENDING → PAID → SHIPPED → COMPLETED
    Rules enforced:
    - PENDING: buyer can cancel, seller cannot ship
    - PAID: seller verified payment slip, can generate delivery slip
    - SHIPPED: stock deducted, order is locked
    - COMPLETED: order archived
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending — awaiting payment'),
        ('PAID', 'Paid — payment verified'),
        ('SHIPPED', 'Shipped — delivery slip printed'),
        ('COMPLETED', 'Completed — delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        help_text="User who placed this order"
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Auto-generated unique order number"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Sum of all order items"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sale_orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Auto-generate order number on first save."""
        if not self.order_number:
            self.order_number = f"SO-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} — {self.buyer.username} ({self.status})"


class OrderItem(models.Model):
    """
    Individual product line in an order.
    Stores unit_price at time of purchase (price may change later).
    """

    order = models.ForeignKey(
        SaleOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price at time of purchase (snapshot)"
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="quantity × unit_price"
    )

    class Meta:
        db_table = 'order_items'

    def save(self, *args, **kwargs):
        """Auto-calculate subtotal."""
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"


class Payment(models.Model):
    """
    Payment record for an order.
    Flow: Buyer uploads slip → status=PENDING → Seller verifies → VERIFIED/REJECTED
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending verification'),
        ('VERIFIED', 'Verified by seller'),
        ('REJECTED', 'Rejected by seller'),
    ]

    order = models.OneToOneField(
        SaleOrder,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    amount_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount buyer paid"
    )
    # Payment slip image (buyer uploads transfer receipt)
    payment_slip = models.ImageField(
        upload_to='payment_slips/',
        blank=True,
        null=True,
        help_text="Transfer receipt / payment proof image"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    payment_method = models.CharField(
        max_length=50,
        default='bank_transfer',
        help_text="e.g. bank_transfer, promptpay"
    )
    note = models.TextField(
        blank=True,
        default='',
        help_text="Seller's note on verification"
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When buyer made the payment"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"Payment for {self.order.order_number} — {self.status}"


class DeliverySlip(models.Model):
    """
    Delivery slip for shipping.
    - Generated when seller is ready to ship (order must be PAID)
    - Printing triggers stock deduction via Celery task
    - slip_number: unique ID printed on the package label
    """

    order = models.OneToOneField(
        SaleOrder,
        on_delete=models.CASCADE,
        related_name='delivery_slip'
    )
    slip_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Unique slip number for package label"
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Shipping carrier tracking number"
    )
    stock_deducted = models.BooleanField(
        default=False,
        help_text="True after Celery task deducted stock"
    )
    printed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the slip was printed"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'delivery_slips'

    def save(self, *args, **kwargs):
        """Auto-generate slip number on first save."""
        if not self.slip_number:
            self.slip_number = f"DS-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Slip {self.slip_number} for {self.order.order_number}"
