from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Min
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
    list_select_related = ["seller", "category"]

    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "seller")}),
        ("Categoria", {"fields": ("category",)}),
        ("Preço", {"fields": ("base_price", "image")}),
        ("Estado", {"fields": ("is_active",)}),
        ("Datas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(min_variant_price=Min("variants__price"))

    def base_price_display(self, obj):
        price = obj.min_variant_price if obj.min_variant_price is not None else obj.base_price
        return format_html("${}", price)

    base_price_display.short_description = "Preço"
    base_price_display.admin_order_field = "base_price"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["sku", "product", "name", "price", "stock", "is_active"]
    list_filter = ["is_active", "product"]
    search_fields = ["sku", "name", "product__name"]
