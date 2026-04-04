from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart_view, name="view"),
    path("add/", views.cart_add_view, name="add"),
    path("remove/<int:item_id>/", views.cart_remove_view, name="remove"),
    path("update/<int:item_id>/", views.cart_update_view, name="update"),
    path("clear/", views.cart_clear_view, name="clear"),
]
