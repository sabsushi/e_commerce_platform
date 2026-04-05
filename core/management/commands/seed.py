"""
Seed the database with demo data so the app is immediately usable.
Run with: python manage.py seed
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = "Seed the database with demo categories, products, and users"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")
        with transaction.atomic():
            self._create_superuser()
            self._create_buyer()
            seller = self._create_seller()
            categories = self._create_categories()
            self._create_products(categories, seller)
        self.stdout.write(self.style.SUCCESS("Done! Database seeded successfully."))
        self.stdout.write("")
        self.stdout.write("  Admin login  : admin / admin123")
        self.stdout.write("  Buyer login  : buyer / buyer123")
        self.stdout.write("  Seller login : seller / seller123")
        self.stdout.write("  App URL      : http://127.0.0.1:8000/")

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _create_superuser(self):
        if User.objects.filter(username="admin").exists():
            self.stdout.write("  [skip] superuser 'admin' already exists")
            return
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
        )
        self.stdout.write("  [ok] superuser 'admin' created")

    def _create_buyer(self):
        if User.objects.filter(username="buyer").exists():
            self.stdout.write("  [skip] user 'buyer' already exists")
            return
        User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="buyer123",
        )
        self.stdout.write("  [ok] user 'buyer' created")

    def _create_seller(self):
        from users.models import Profile

        if User.objects.filter(username="seller").exists():
            self.stdout.write("  [skip] user 'seller' already exists")
            return User.objects.get(username="seller")
        seller = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="seller123",
        )
        Profile.objects.filter(user=seller).update(role=Profile.Role.SELLER)
        self.stdout.write("  [ok] user 'seller' created (role: Seller)")
        return seller

    def _create_categories(self):
        from products.models import Category

        data = [
            {"name": "Electronics", "slug": "electronics", "description": "Gadgets and devices"},
            {"name": "Clothing", "slug": "clothing", "description": "Apparel and accessories"},
            {"name": "Books", "slug": "books", "description": "Physical and digital books"},
            {"name": "Software", "slug": "software", "description": "Digital software licenses"},
        ]

        categories = {}
        for item in data:
            obj, created = Category.objects.get_or_create(
                slug=item["slug"],
                defaults={"name": item["name"], "description": item["description"]},
            )
            categories[item["slug"]] = obj
            status = "[ok]" if created else "[skip]"
            self.stdout.write(f"  {status} category '{item['name']}'")

        # Sub-category example
        phones, created = Category.objects.get_or_create(
            slug="phones",
            defaults={
                "name": "Phones",
                "parent": categories["electronics"],
                "description": "Smartphones and accessories",
            },
        )
        categories["phones"] = phones
        self.stdout.write(f"  {'[ok]' if created else '[skip]'} category 'Phones'")

        return categories

    def _create_products(self, categories, seller):
        from products.models import Product, ProductVariant

        products_data = [
            {
                "name": "Wireless Headphones",
                "slug": "wireless-headphones",
                "description": "Premium noise-cancelling wireless headphones with 30h battery life.",
                "category": categories["electronics"],
                "base_price": "79.99",
                "seller": seller,
                "variants": [
                    {"sku": "WH-BLK", "name": "Black", "price": "79.99", "stock": 50},
                    {"sku": "WH-WHT", "name": "White", "price": "79.99", "stock": 30},
                ],
            },
            {
                "name": "Smartphone Pro X",
                "slug": "smartphone-pro-x",
                "description": "Latest flagship smartphone with 6.7\" display and triple camera.",
                "category": categories["phones"],
                "base_price": "699.99",
                "seller": seller,
                "variants": [
                    {"sku": "SPX-128", "name": "128 GB", "price": "699.99", "stock": 20},
                    {"sku": "SPX-256", "name": "256 GB", "price": "799.99", "stock": 15},
                ],
            },
            {
                "name": "Classic White Tee",
                "slug": "classic-white-tee",
                "description": "100% organic cotton unisex t-shirt.",
                "category": categories["clothing"],
                "base_price": "19.99",
                "seller": seller,
                "variants": [
                    {"sku": "CWT-S", "name": "Small", "price": "19.99", "stock": 100},
                    {"sku": "CWT-M", "name": "Medium", "price": "19.99", "stock": 120},
                    {"sku": "CWT-L", "name": "Large", "price": "19.99", "stock": 80},
                ],
            },
            {
                "name": "Django for Beginners",
                "slug": "django-for-beginners",
                "description": "A hands-on guide to building web apps with Django.",
                "category": categories["books"],
                "base_price": "34.99",
                "seller": seller,
                "variants": [
                    {"sku": "DFB-PB", "name": "Paperback", "price": "34.99", "stock": 200},
                ],
            },
            {
                "name": "Python Mastery eBook",
                "slug": "python-mastery-ebook",
                "description": "Complete Python guide — instant download, 500+ pages.",
                "category": categories["books"],
                "base_price": "14.99",
                "seller": seller,
                "variants": [
                    {"sku": "PME-DIG", "name": "Digital Download", "price": "14.99", "stock": 0},
                ],
            },
            {
                "name": "DevTools Pro License",
                "slug": "devtools-pro-license",
                "description": "1-year developer tooling license. Delivered via email.",
                "category": categories["software"],
                "base_price": "49.99",
                "seller": seller,
                "variants": [
                    {"sku": "DTP-1Y", "name": "1-Year License", "price": "49.99", "stock": 0},
                ],
            },
        ]

        for pd in products_data:
            variants_data = pd.pop("variants")
            product, created = Product.objects.get_or_create(
                slug=pd["slug"],
                defaults=pd,
            )
            status = "[ok]" if created else "[skip]"
            self.stdout.write(f"  {status} product '{product.name}'")

            for vd in variants_data:
                _, vcreated = ProductVariant.objects.get_or_create(
                    sku=vd["sku"],
                    defaults={"product": product, **vd},
                )
