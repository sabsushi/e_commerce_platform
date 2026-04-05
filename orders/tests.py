from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Profile
from products.models import Category, Product, ProductVariant
from orders.models import Order, OrderItem

User = get_user_model()


def make_seller(username):
    user = User.objects.create_user(username=username, password="pass")
    profile = Profile.objects.get(user=user)
    profile.role = Profile.Role.SELLER
    profile.save()
    return user


def make_buyer(username):
    user = User.objects.create_user(username=username, password="pass")
    return user


def make_product(seller, name, category):
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="desc",
        category=category,
        base_price="10.00",
        seller=seller,
    )


def make_variant(product, sku):
    return ProductVariant.objects.create(
        product=product,
        sku=sku,
        name="default",
        price="10.00",
        stock=100,
    )


def make_order(buyer, variant, quantity=1):
    order = Order.objects.create(buyer=buyer, total_amount=10)
    OrderItem.objects.create(
        order=order, variant=variant, quantity=quantity, unit_price="10.00"
    )
    return order


class SellerOrdersViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Electronics", slug="electronics")

        self.seller = make_seller("seller1")
        self.other_seller = make_seller("seller2")
        self.buyer = make_buyer("buyer1")

        self.product = make_product(self.seller, "Widget", self.category)
        self.variant = make_variant(self.product, "SKU-WIDGET-1")

        self.other_product = make_product(self.other_seller, "Gadget", self.category)
        self.other_variant = make_variant(self.other_product, "SKU-GADGET-1")

        # Order containing seller's product
        self.own_order = make_order(self.buyer, self.variant)

        # Order containing only the other seller's product
        self.unrelated_order = make_order(self.buyer, self.other_variant)

    def test_seller_sees_own_orders(self):
        self.client.login(username="seller1", password="pass")
        response = self.client.get(reverse("orders:seller_orders"))
        self.assertEqual(response.status_code, 200)
        ids = [o["id"] for o in response.data["results"]]
        self.assertIn(self.own_order.id, ids)

    def test_seller_does_not_see_unrelated_orders(self):
        self.client.login(username="seller1", password="pass")
        response = self.client.get(reverse("orders:seller_orders"))
        self.assertEqual(response.status_code, 200)
        ids = [o["id"] for o in response.data["results"]]
        self.assertNotIn(self.unrelated_order.id, ids)

    def test_buyer_is_forbidden(self):
        self.client.login(username="buyer1", password="pass")
        response = self.client.get(reverse("orders:seller_orders"))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_is_forbidden(self):
        response = self.client.get(reverse("orders:seller_orders"))
        self.assertEqual(response.status_code, 403)
