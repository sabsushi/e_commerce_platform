from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from users.models import Profile
from .models import Product, Category


def is_seller(user):
    return Profile.objects.filter(user=user, role=Profile.Role.SELLER).exists()


def product_to_dict(product):
    variants = list(product.variants.all())
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "base_price": str(product.base_price),
        "category": {
            "id": product.category.id,
            "name": product.category.name,
            "slug": product.category.slug,
        },
        "variants": [
            {
                "id": v.id,
                "sku": v.sku,
                "name": v.name,
                "price": str(v.price),
                "stock": v.stock,
            }
            for v in variants
        ],
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


def product_list_dict(product):
    variants = list(product.variants.all())
    min_price = min((v.price for v in variants), default=product.base_price)
    total_stock = sum(v.stock for v in variants) if variants else 0
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "base_price": str(min_price),
        "category_name": product.category.name,
        "stock": total_stock,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("variants")
    )

    ordering = request.GET.get("ordering", "-created_at")
    allowed_ordering = {
        "name",
        "base_price",
        "created_at",
        "-name",
        "-base_price",
        "-created_at",
    }
    if ordering in allowed_ordering:
        products = products.order_by(ordering)

    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    min_price = request.GET.get("min_price")
    if min_price:
        products = products.filter(base_price__gte=min_price)

    max_price = request.GET.get("max_price")
    if max_price:
        products = products.filter(base_price__lte=max_price)

    paginator = Paginator(products, 10)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    results = [product_list_dict(p) for p in page_obj]
    return Response(
        {
            "count": paginator.count,
            "pages": paginator.num_pages,
            "page": page_obj.number,
            "results": results,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("variants"),
        pk=pk,
        is_active=True,
    )
    return Response(product_to_dict(product))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def product_create(request):
    if not is_seller(request.user):
        return Response(
            {"detail": "Apenas sellers podem criar produtos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    data = request.data
    required_fields = ["name", "description", "base_price", "category"]
    for field in required_fields:
        if field not in data:
            return Response(
                {field: ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        category = Category.objects.get(pk=data["category"])
    except Category.DoesNotExist:
        return Response(
            {"category": ["Category not found."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    product = Product.objects.create(
        name=data["name"],
        description=data["description"],
        base_price=data["base_price"],
        category=category,
        seller=request.user,
    )
    return Response(product_to_dict(product), status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def product_update(request, pk):
    if not is_seller(request.user):
        return Response(
            {"detail": "Apenas sellers podem atualizar produtos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    product = get_object_or_404(Product.objects.prefetch_related("variants"), pk=pk)

    data = request.data
    if "name" in data:
        product.name = data["name"]
    if "description" in data:
        product.description = data["description"]
    if "base_price" in data:
        product.base_price = data["base_price"]
    if "category" in data:
        try:
            product.category = Category.objects.get(pk=data["category"])
        except Category.DoesNotExist:
            return Response(
                {"category": ["Category not found."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    product.save()
    return Response(product_to_dict(product))


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def product_delete(request, pk):
    if not is_seller(request.user):
        return Response(
            {"detail": "Apenas sellers podem eliminar produtos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    product = get_object_or_404(Product, pk=pk)

    product.is_active = False
    product.save()
    return Response({"detail": "Produto desativado com sucesso."})


@api_view(["GET"])
@permission_classes([AllowAny])
def product_search(request):
    q = request.GET.get("q", "").strip()
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("variants")
    )

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    ordering = request.GET.get("ordering", "-created_at")
    allowed_ordering = {
        "name",
        "base_price",
        "created_at",
        "-name",
        "-base_price",
        "-created_at",
    }
    if ordering in allowed_ordering:
        products = products.order_by(ordering)

    min_price = request.GET.get("min_price")
    if min_price:
        products = products.filter(base_price__gte=min_price)

    max_price = request.GET.get("max_price")
    if max_price:
        products = products.filter(base_price__lte=max_price)

    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    paginator = Paginator(products, 24)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    results = [product_list_dict(p) for p in page_obj]
    return Response(
        {
            "count": paginator.count,
            "pages": paginator.num_pages,
            "page": page_obj.number,
            "results": results,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def category_list(request):
    categories = Category.objects.all()
    results = [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
        }
        for c in categories
    ]
    return Response(results)


# --- HTML Views ---

def product_list_view(request):
    from django.db.models import Sum
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "seller")
        .prefetch_related("variants")
        .annotate(total_stock=Sum("variants__stock"))
    )

    categories = Category.objects.all()
    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    q = request.GET.get("q")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    products = products.order_by("-created_at")

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "products/product_list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": category_slug,
        "q": q or "",
    })


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return render(request, "products/product_detail.html", {"product": product})
