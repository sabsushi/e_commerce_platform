from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout_view, name="checkout"),
    path("checkout/html/", views.checkout_html_view, name="checkout_html"),
    path("", views.order_list_view, name="list"),
    path("<int:pk>/", views.order_detail_view, name="detail"),
    path("<int:pk>/confirm/", views.confirm_order_view, name="confirm"),
    path("<int:pk>/cancel/", views.cancel_order_view, name="cancel"),
    path("seller/", views.seller_orders_view, name="seller_orders"),
    path(
        "<int:order_id>/items/<int:item_id>/fulfil/",
        views.seller_fulfil_view,
        name="seller_fulfil",
    ),
    path("summary/", views.order_summary_view, name="summary"),
]
