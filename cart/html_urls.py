from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_page_view, name="page"),
    path("add/", views.cart_add_html, name="add_html"),
    path("remove/<int:item_id>/", views.cart_remove_html, name="remove_html"),
]
