# ===========================================
# Celery Tasks — Background Processing
# deduct_stock: ลด stock เมื่อ print ใบส่งของ (ข้อ 1.7)
# Atomic transaction ป้องกัน race condition
# ===========================================
import logging
from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def deduct_stock_task(self, order_id):
    """
    ลด stock สินค้าทั้งหมดใน order (ข้อ 1.7)
    เรียกเมื่อ: ผู้ขาย print ใบส่งของ
    - ลด quantity ของแต่ละ product
    - บันทึก StockLog
    - อัปเดต delivery_slip.stock_deducted = True
    """
    from orders.models import SaleOrder, DeliverySlip
    from products.models import StockLog

    try:
        with transaction.atomic():
            order = SaleOrder.objects.select_for_update().get(id=order_id)
            delivery_slip = order.delivery_slip

            # ข้ามถ้าลด stock ไปแล้ว
            if delivery_slip.stock_deducted:
                logger.warning(f"Stock already deducted for order {order.order_number}")
                return

            # ลด stock ทุก item ใน order
            for item in order.items.select_related('product').all():
                product = item.product
                product.quantity -= item.quantity
                product.save(update_fields=['quantity'])

                # บันทึก log
                StockLog.objects.create(
                    product=product,
                    quantity_change=-item.quantity,
                    reason='ORDER_SHIPPED',
                    note=f'Order {order.order_number} — shipped'
                )

            # อัปเดต delivery slip
            delivery_slip.stock_deducted = True
            delivery_slip.save(update_fields=['stock_deducted'])

        logger.info(f"Stock deducted for order {order.order_number}")

    except Exception as exc:
        logger.error(f"Stock deduction failed for order {order_id}: {exc}")
        self.retry(exc=exc, countdown=10)
