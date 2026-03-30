from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Category, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    readonly_fields = ["id"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "product_count"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Produtos"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "product_type",
        "base_price_display",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "product_type", "category", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductVariantInline]

    fieldsets = (
        (None, {"fields": ("name", "slug", "description")}),
        ("Tipo e Categoria", {"fields": ("product_type", "category")}),
        ("Preço", {"fields": ("base_price", "image")}),
        ("Estado", {"fields": ("is_active",)}),
        ("Datas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def base_price_display(self, obj):
        if obj.variants.exists():
            min_price = min(v.price for v in obj.variants.all())
            return format_html(f"${min_price}")
        return format_html(f"${obj.base_price}")

    base_price_display.short_description = "Preço"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["sku", "product", "name", "price", "stock", "is_active"]
    list_filter = ["is_active", "product"]
    search_fields = ["sku", "name", "product__name"]
