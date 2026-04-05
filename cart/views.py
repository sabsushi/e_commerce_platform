import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Profile
from .models import Cart, CartItem
from .services import (
    get_cart_contents,
    add_to_cart,
    remove_from_cart,
    update_cart_item,
    clear_cart,
)


def is_buyer(user):
    try:
        return user.profile.role == Profile.Role.BUYER
    except Profile.DoesNotExist:
        return False


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_view(request):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem acessar o carrinho."},
            status=status.HTTP_403_FORBIDDEN,
        )

    cart_data = get_cart_contents(request.user)
    return Response(cart_data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_add_view(request):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem adicionar itens ao carrinho."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        data = request.data
        variant_id = data.get("variant_id")
        quantity = int(data.get("quantity", 1))

        if not variant_id:
            return Response(
                {"variant_id": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity <= 0:
            return Response(
                {"quantity": ["Quantity must be greater than 0."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = add_to_cart(request.user, variant_id, quantity)
        return Response(
            {
                "id": item.id,
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "subtotal": str(item.subtotal),
            },
            status=status.HTTP_201_CREATED,
        )
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cart_remove_view(request, item_id):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem remover itens do carrinho."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        remove_from_cart(request.user, item_id)
        return Response({"detail": "Item removed from cart."})
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def cart_update_view(request, item_id):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem atualizar itens do carrinho."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        quantity = int(request.data.get("quantity", 1))

        if quantity <= 0:
            remove_from_cart(request.user, item_id)
            return Response({"detail": "Item removed from cart."})

        item = update_cart_item(request.user, item_id, quantity)

        if item is None:
            return Response({"detail": "Item removed from cart."})

        return Response(
            {
                "id": item.id,
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "subtotal": str(item.subtotal),
            }
        )
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_clear_view(request):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem limpar o carrinho."},
            status=status.HTTP_403_FORBIDDEN,
        )

    clear_cart(request.user)
    return Response({"detail": "Cart cleared successfully."})


# ── HTML views ────────────────────────────────────────────────────────────────

@login_required
def cart_page_view(request):
    if not is_buyer(request.user):
        messages.error(request, "Only buyers can access the cart.")
        return redirect("product_list")

    cart = Cart.objects.filter(buyer=request.user, status=Cart.Status.OPEN).first()
    items = (
        CartItem.objects.filter(cart=cart)
        .select_related("variant", "variant__product")
        if cart else []
    )
    subtotal = cart.subtotal if cart else 0
    return render(request, "cart/cart.html", {"items": items, "subtotal": subtotal})


@login_required
@require_POST
def cart_add_html(request):
    if not is_buyer(request.user):
        messages.error(request, "Only buyers can add items to the cart.")
        return redirect("product_list")

    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))
    next_url = request.POST.get("next", "product_list")

    try:
        add_to_cart(request.user, variant_id, quantity)
        messages.success(request, "Item added to cart.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(next_url)


@login_required
@require_POST
def cart_remove_html(request, item_id):
    if is_buyer(request.user):
        try:
            remove_from_cart(request.user, item_id)
            messages.success(request, "Item removed from cart.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("cart:page")
