from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Profile
from .models import Order, OrderStatus
from .services import (
    checkout,
    confirm_order,
    cancel_order,
    fulfil_item,
    get_seller_orders,
    get_order_summary,
)


def is_buyer(user):
    try:
        return user.profile.role == Profile.Role.BUYER
    except Profile.DoesNotExist:
        return False


def is_seller(user):
    try:
        return user.profile.role == Profile.Role.SELLER
    except Profile.DoesNotExist:
        return False


def order_to_dict(order):
    return {
        "id": order.id,
        "buyer": {
            "id": order.buyer.id,
            "username": order.buyer.username,
        },
        "status": order.status,
        "total_amount": str(order.total_amount),
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "items": [
            {
                "id": item.id,
                "variant": {
                    "id": item.variant.id,
                    "sku": item.variant.sku,
                    "name": item.variant.name,
                    "product": {
                        "id": item.variant.product.id,
                        "name": item.variant.product.name,
                    },
                },
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal),
                "fulfilment_status": item.fulfilment_status,
            }
            for item in order.items.all()
        ],
    }


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def checkout_view(request):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem fazer checkout."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        order = checkout(request.user)
        return Response(
            order_to_dict(order),
            status=status.HTTP_201_CREATED,
        )
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail_view(request, pk):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem visualizar pedidos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    order = (
        Order.objects.prefetch_related("items__variant__product", "buyer")
        .filter(buyer=request.user, pk=pk)
        .first()
    )

    if not order:
        return Response(
            {"detail": "Order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(order_to_dict(order))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_list_view(request):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem visualizar pedidos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    orders = (
        Order.objects.filter(buyer=request.user)
        .prefetch_related("items__variant__product")
        .order_by("-created_at")
    )

    paginator = Paginator(orders, 20)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    results = [order_to_dict(o) for o in page_obj]
    return Response(
        {
            "count": paginator.count,
            "pages": paginator.num_pages,
            "page": page_obj.number,
            "results": results,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_order_view(request, pk):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem confirmar pedidos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        order = confirm_order(request.user, pk)
        return Response({"detail": "Order confirmed.", "status": order.status})
    except Order.DoesNotExist:
        return Response(
            {"detail": "Order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_order_view(request, pk):
    if not is_buyer(request.user):
        return Response(
            {"detail": "Apenas buyers podem cancelar pedidos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        order = cancel_order(request.user, pk)
        return Response({"detail": "Order cancelled.", "status": order.status})
    except Order.DoesNotExist:
        return Response(
            {"detail": "Order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@login_required
@require_POST
def checkout_html_view(request):
    if not is_buyer(request.user):
        messages.error(request, "Only buyers can checkout.")
        return redirect("cart:page")

    try:
        order = checkout(request.user)
        messages.success(request, f"Order #{order.id} placed successfully!")
        return render(request, "orders/order_success.html", {"order": order})
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("cart:page")


@login_required
def seller_orders_view(request):
    if not is_seller(request.user):
        return render(request, "orders/seller_orders.html", {"page_obj": None, "forbidden": True}, status=403)

    orders = get_seller_orders(request.user)

    paginator = Paginator(orders, 20)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    return render(request, "orders/seller_orders.html", {"page_obj": page_obj})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def seller_fulfil_view(request, order_id, item_id):
    if not is_seller(request.user):
        return Response(
            {"detail": "Apenas sellers podem marcar itens como enviados."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        item = fulfil_item(request.user, order_id, item_id)
        return Response(
            {
                "detail": "Item marked as fulfilled.",
                "fulfilment_status": item.fulfilment_status,
            }
        )
    except Order.DoesNotExist:
        return Response(
            {"detail": "Order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_summary_view(request):
    if not is_seller(request.user):
        return Response(
            {"detail": "Apenas sellers podem visualizar summaries."},
            status=status.HTTP_403_FORBIDDEN,
        )

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    summary = get_order_summary(request.user, start_date, end_date)
    return Response(summary)
