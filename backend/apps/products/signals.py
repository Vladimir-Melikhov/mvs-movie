"""
File: backend/apps/products/signals.py
Purpose: Signal handlers for product models
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Product, ProductVariant


@receiver(pre_save, sender=Product)
def update_product_stock(sender, instance, **kwargs):
    """
    Update product total stock based on variants.
    """
    if instance.pk:
        total_stock = sum(
            instance.variants.filter(is_deleted=False, is_active=True).values_list(
                "stock_quantity", flat=True
            )
        )
        instance.stock_quantity = total_stock


@receiver(post_save, sender=ProductVariant)
def update_parent_product_stock(sender, instance, **kwargs):
    """
    Update parent product stock when variant stock changes.
    """
    product = instance.product
    total_stock = sum(
        product.variants.filter(is_deleted=False, is_active=True).values_list(
            "stock_quantity", flat=True
        )
    )
    Product.objects.filter(pk=product.pk).update(stock_quantity=total_stock)
