from django.urls import path

from .views import (
    product_list,
    product_detail,
    product_create,
    product_update,
    product_delete,
    product_search,
    category_list,
)

urlpatterns = [
    path("products/", product_list, name="product-list"),
    path("products/search/", product_search, name="product-search"),
    path("products/create/", product_create, name="product-create"),
    path("products/<int:pk>/", product_detail, name="product-detail"),
    path("products/<int:pk>/update/", product_update, name="product-update"),
    path("products/<int:pk>/delete/", product_delete, name="product-delete"),
    path("categories/", category_list, name="category-list"),
]
