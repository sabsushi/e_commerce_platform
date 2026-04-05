from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import Product, Category, ProductVariant

User = get_user_model()


def seller_users_queryset():
    from users.models import Profile
    seller_ids = Profile.objects.filter(role=Profile.Role.SELLER).values_list("user_id", flat=True)
    return User.objects.filter(pk__in=seller_ids)


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["seller"].queryset = seller_users_queryset()
        self.fields["seller"].help_text = "Only users with the Seller role are listed."

    def clean_seller(self):
        seller = self.cleaned_data.get("seller")
        if seller:
            from users.models import Profile
            if not Profile.objects.filter(user=seller, role=Profile.Role.SELLER).exists():
                raise ValidationError("This user does not have the Seller role.")
        return seller


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
    form = ProductAdminForm
    list_display = [
        "name",
        "seller",
        "category",
        "base_price_display",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["name", "description", "seller__username"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductVariantInline]

    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "seller")}),
        ("Categoria", {"fields": ("category",)}),
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
