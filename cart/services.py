from django.db import transaction
from django.contrib.auth import get_user_model

from products.models import ProductVariant
from .models import Cart, CartItem

User = get_user_model()


def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(buyer=user, status=Cart.Status.OPEN)
    return cart


def add_to_cart(user, variant_id, quantity=1):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    cart = get_or_create_cart(user)

    with transaction.atomic():
        try:
            variant = ProductVariant.objects.select_for_update().get(pk=variant_id, is_active=True)
        except ProductVariant.DoesNotExist:
            raise ValueError("Product variant not found or inactive")

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, variant=variant, defaults={"quantity": 0}
        )

        new_quantity = cart_item.quantity + quantity
        if variant.stock < new_quantity:
            raise ValueError("Insufficient stock for requested quantity")

        cart_item.quantity = new_quantity
        cart_item.save()

    return cart_item


def remove_from_cart(user, item_id):
    cart = get_or_create_cart(user)

    try:
        cart_item = CartItem.objects.get(pk=item_id, cart=cart)
    except CartItem.DoesNotExist:
        raise ValueError("Cart item not found")

    cart_item.delete()
    return True


def update_cart_item(user, item_id, quantity):
    cart = get_or_create_cart(user)

    try:
        cart_item = CartItem.objects.select_related("variant").get(
            pk=item_id, cart=cart
        )
    except CartItem.DoesNotExist:
        raise ValueError("Cart item not found")

    if quantity <= 0:
        cart_item.delete()
        return None

    if cart_item.variant.stock < quantity:
        raise ValueError("Insufficient stock")

    cart_item.quantity = quantity
    cart_item.save()

    return cart_item


def clear_cart(user):
    cart = get_or_create_cart(user)
    CartItem.objects.filter(cart=cart).delete()
    return True


def get_cart_contents(user):
    cart = get_or_create_cart(user)
    items = CartItem.objects.filter(cart=cart).select_related(
        "variant", "variant__product", "variant__product__category"
    )

    return {
        "cart_id": cart.id,
        "status": cart.status,
        "items": [
            {
                "id": item.id,
                "variant": {
                    "id": item.variant.id,
                    "sku": item.variant.sku,
                    "name": item.variant.name,
                    "price": str(item.variant.price),
                    "stock": item.variant.stock,
                    "product": {
                        "id": item.variant.product.id,
                        "name": item.variant.product.name,
                        "image": item.variant.product.image.url
                        if item.variant.product.image
                        else None,
                    },
                },
                "quantity": item.quantity,
                "subtotal": str(item.subtotal),
                "available": item.variant.stock >= item.quantity,
            }
            for item in items
        ],
        "subtotal": str(cart.subtotal),
    }
