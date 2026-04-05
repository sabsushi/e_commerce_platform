from django.db import transaction
from django.db.models import F


def decrement_stock(variant_id, quantity, user=None):
    from .models import ProductVariant, StockChange

    with transaction.atomic():
        updated = ProductVariant.objects.filter(pk=variant_id, stock__gte=quantity).update(
            stock=F("stock") - quantity
        )
        if updated == 0:
            raise ValueError(f"Insufficient stock for variant {variant_id}")

        variant = ProductVariant.objects.select_related("product").get(pk=variant_id)
        StockChange.objects.create(
            product=variant.product,
            variant=variant,
            change_qty=-quantity,
            reason="order",
            user=user,
        )


def restock(variant_id, quantity, user):
    from .models import ProductVariant, StockChange

    with transaction.atomic():
        ProductVariant.objects.filter(pk=variant_id).update(stock=F("stock") + quantity)
        variant = ProductVariant.objects.select_related("product").get(pk=variant_id)
        StockChange.objects.create(
            product=variant.product,
            variant=variant,
            change_qty=quantity,
            reason="restock",
            user=user,
        )


def restore_stock(variant_id, quantity, user=None):
    from .models import ProductVariant, StockChange

    with transaction.atomic():
        ProductVariant.objects.filter(pk=variant_id).update(stock=F("stock") + quantity)
        variant = ProductVariant.objects.select_related("product").get(pk=variant_id)
        StockChange.objects.create(
            product=variant.product,
            variant=variant,
            change_qty=quantity,
            reason="order_cancelled",
            user=user,
        )
