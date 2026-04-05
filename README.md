# e-Commerce Platform

A demonstration e-commerce web application built with Django. It supports two user roles — **Buyers** and **Sellers** — each with their own dedicated workflows, from browsing and purchasing products to listing and managing orders.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture & Technical Decisions](#architecture--technical-decisions)
- [Data Model](#data-model)
- [Getting Started](#getting-started)
- [Default Accounts](#default-accounts)
- [Using the Website](#using-the-website)
  - [As a Buyer](#as-a-buyer)
  - [As a Seller](#as-a-seller)
  - [As an Admin](#as-an-admin)
- [URL Reference](#url-reference)
- [REST API Reference](#rest-api-reference)
- [Running Tests](#running-tests)
- [Contributors](#contributors)

---

## Features

- **Two-role system** — users are either Buyers or Sellers, each with distinct permissions
- **Product catalogue** — categories (with sub-categories), product variants (e.g. size/colour), stock tracking, and product images
- **Shopping cart** — session-based cart with add, update, and remove actions; cart count shown in the navbar
- **Checkout & Orders** — buyers can checkout, confirm and cancel orders; order lifecycle is enforced via status transitions
- **Seller dashboard** — sellers can create/edit/deactivate their own products and view orders containing their items, with item-level fulfilment
- **Public seller profiles** — every seller has a public profile page showing their bio and active listings
- **Stock management** — stock is decremented on checkout and restored on cancellation; every change is logged
- **Admin panel** — full Django admin with inline variants, role-aware seller selector, and per-role filters
- **REST API** — JSON API for cart operations, product search, and order management

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Django 4.2 |
| Language | Python 3.9+ |
| Database | SQLite (development) |
| Frontend | Django Templates + Bootstrap 5 |
| API | Django REST Framework |
| Image processing | Pillow |

---

## Architecture & Technical Decisions

### Why Django?

Django was chosen for its "batteries included" philosophy — built-in ORM, admin panel, authentication system, form validation, and migrations meant we could focus on business logic rather than plumbing. The Django admin alone saved significant time by giving us a fully functional back-office for managing users, products, and orders without writing a single admin view.

### Why Django REST Framework for the API?

The project has two distinct interaction patterns: HTML pages rendered server-side (browsing, cart, checkout) and JSON endpoints for programmatic access (cart operations, order management, product CRUD for sellers). DRF was used exclusively for the JSON layer, keeping template views and API views cleanly separated into `urls.py` and `api_urls.py` per app. This avoids the complexity of a full SPA while still exposing a proper API.

### Why SQLite?

This is a demonstration project — SQLite requires zero configuration, ships with Python, and is more than sufficient for local development and evaluation. The Django ORM abstracts the database layer entirely, so migrating to PostgreSQL for production would require only a settings change and no code modifications.

### Services Layer

Business logic lives in `services.py` inside each app rather than in views or models. This keeps views thin (they only handle HTTP concerns) and makes the logic independently testable. For example:

- `orders/services.py` — handles checkout (stock decrement, order creation, cart close) inside a single `transaction.atomic()` block, ensuring no partial state if anything fails
- `products/services.py` — all stock mutations go through `decrement_stock` / `restore_stock`, which also write an audit entry to `StockChange` on every call
- `orders/services.py:cancel_order` — enforces a 30-minute cancellation window and restores stock atomically

### Role-based Access Control

User roles (Buyer / Seller) are stored on a `Profile` model with a `OneToMany` relation to Django's built-in `User`. Roles are enforced at the view level — API endpoints return `403` if the role doesn't match, and HTML views redirect with an error message. A `post_save` signal on `User` automatically creates a `Profile` with the default `buyer` role on registration, so no user is ever without a role.

### Stock Integrity

Stock decrements use a conditional `UPDATE` query (`stock__gte=quantity`) rather than a read-then-write pattern, preventing race conditions when two buyers try to purchase the last item simultaneously. Every stock change (order, restock, cancellation) is recorded in `StockChange` for a full audit trail.

### Cart Design

The cart is persisted in the database (not just the session) so it survives browser restarts. Each `Cart` has a status (`open` / `closed`). On checkout the cart is closed atomically with the order creation — it is never deleted, preserving the purchase history.

---

## Data Model

```
User (Django built-in)
 └── Profile          role: buyer | seller

Category
 └── Category         (self-referential, max 2 levels deep)

Product
 ├── Category         FK — protected on delete
 ├── User (seller)    FK — nullable
 └── ProductVariant[] sku, price, stock
      └── StockChange  audit log of every stock movement

Cart
 ├── User (buyer)
 └── CartItem[]
      └── ProductVariant

Order
 ├── User (buyer)
 └── OrderItem[]      unit_price snapshotted at creation time
      └── ProductVariant
```

**Key modelling decisions:**

- `unit_price` on `OrderItem` is written once at checkout and never updated — the price a customer paid is immutable even if the product price changes later
- `base_price` on `Product` is the fallback display price; the actual selling price lives on `ProductVariant`
- `is_active` on `Product` and `ProductVariant` is a soft-delete flag — records are never hard-deleted, preserving referential integrity for historical orders
- All money fields use `DecimalField` — never `FloatField` — to avoid floating-point rounding errors
- Order status transitions are enforced in a `transition_status()` model method, not scattered across views

---

## Getting Started

### Prerequisites

- Python 3.9+
- [`uv`](https://github.com/astral-sh/uv) (recommended) **or** pip

---

### Just want to try it out?

```bash
make setup
```

That's it. One command installs everything, creates the database, loads demo data, and opens the server at `http://127.0.0.1:8000/`.

> The database file (`db.sqlite3`) is not included in the repository — `make setup` creates it from scratch automatically.

---

### Step-by-step

```bash
make install   # install Python dependencies
make migrate   # create the database and apply migrations
make seed      # load demo categories, products, and users
make run       # start the dev server at http://127.0.0.1:8000/
```

### Other useful commands

```bash
make test    # run the full test suite
make reset   # wipe the database, re-migrate, and re-seed
```

---

## Default Accounts

After running `make seed` (or `make setup`) the following accounts are available:

| Role | Username | Password | Access |
|---|---|---|---|
| Admin | `admin` | `admin123` | Django admin + all features |
| Buyer | `buyer` | `buyer123` | Storefront, cart, checkout |
| Seller | `seller` | `seller123` | Product management, order dashboard |

---

## Using the Website

### As a Buyer

1. **Browse products** — the homepage (`/`) lists all active products. Use the search bar or filter by category.
2. **View a product** — click any product card to see its description, variants, stock level, and seller.
3. **Add to cart** — choose a variant and click **Add to Cart**. The cart count in the top navbar updates immediately.
4. **Manage the cart** — go to `/cart/` to review items, change quantities, or remove items.
5. **Checkout** — click **Proceed to Checkout** in the cart. You must be logged in. The order is placed immediately (payment is mocked).
6. **Order history** — your orders are accessible at `/orders/`. Click any order to see items, prices, and fulfilment status.
7. **Confirm or cancel** — a pending order can be confirmed or cancelled from the order detail view.

> **Note:** only users with the **Buyer** role can add items to the cart or place orders. If you registered without an explicit role, you are a Buyer by default.

---

### As a Seller

1. **Log in** with `seller / seller123` (created by `make seed`) or register at `/users/register/` and ask an admin to set your role to **Seller**.
2. **Create a product** — use the API at `POST /api/products/create/` or the Django admin.
3. **Manage products** — update or soft-delete your products via `PUT /api/products/<id>/update/` and `DELETE /api/products/<id>/delete/`.
4. **View your orders** — go to `/orders/seller/` to see all orders that contain your products, grouped by order.
5. **Fulfil items** — mark individual order items as fulfilled via `POST /orders/<order_id>/items/<item_id>/fulfil/`.
6. **Order summary** — get aggregated sales data at `GET /orders/summary/` (supports `start_date` and `end_date` query params).
7. **Public profile** — your seller profile is publicly visible at `/users/sellers/<username>/`.

> **Note:** Sellers cannot add items to the cart or place orders.

---

### As an Admin

1. Go to `/admin/` and log in with the `admin` account.
2. **Users** — view all users with their roles inline. Change a user's role between Buyer and Seller.
3. **Products** — create/edit products with inline variants. The **Seller** field only lists users with the Seller role.
4. **Categories** — manage the two-level category hierarchy (parent → child).
5. **Orders** — view all orders with status, buyer, total, and line items. Mark items as fulfilled.
6. **Stock changes** — audit log of every stock movement (orders, restocks, manual adjustments, cancellations).

---

## URL Reference

### HTML views

| URL | Description | Auth required |
|---|---|---|
| `/` | Homepage — product listing | No |
| `/products/<id>/` | Product detail page | No |
| `/users/register/` | Register a new account | No |
| `/users/login/` | Log in | No |
| `/users/logout/` | Log out (POST) | Yes |
| `/users/profile/` | View/edit your profile | Yes |
| `/users/sellers/<username>/` | Public seller profile | No |
| `/cart/` | Shopping cart | Yes (Buyer) |
| `/cart/add/` | Add item to cart | Yes (Buyer) |
| `/cart/remove/<item_id>/` | Remove item from cart | Yes (Buyer) |
| `/orders/checkout/html/` | Place order from cart | Yes (Buyer) |
| `/orders/seller/` | Seller order dashboard | Yes (Seller) |

### Admin

| URL | Description |
|---|---|
| `/admin/` | Django administration panel |

---

## REST API Reference

All API endpoints are under `/api/` or `/orders/`.
Authenticated endpoints require a logged-in session cookie. To authenticate via curl, first POST to the login endpoint and save the cookie jar:

```bash
# Log in and save the session cookie
curl -c cookies.txt -X POST http://127.0.0.1:8000/users/login/ \
  -d "username=buyer&password=buyer123"
```

Then pass `-b cookies.txt` on subsequent requests.

### Products

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/products/` | No | List all active products |
| `GET` | `/api/products/<id>/` | No | Product detail |
| `GET` | `/api/products/search/?q=<term>` | No | Search products by name/description |
| `GET` | `/api/categories/` | No | List all categories |
| `POST` | `/api/products/create/` | Seller | Create a new product |
| `PUT` | `/api/products/<id>/update/` | Seller (owner) | Update a product |
| `DELETE` | `/api/products/<id>/delete/` | Seller (owner) | Soft-delete a product |

```bash
# List products
curl http://127.0.0.1:8000/api/products/

# Search
curl "http://127.0.0.1:8000/api/products/search/?q=headphones"

# Create a product (seller only)
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/products/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"My Product","slug":"my-product","description":"..","category":1,"base_price":"9.99"}'
```

### Cart

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/cart/` | Buyer | View current cart |
| `POST` | `/api/cart/add/` | Buyer | Add a variant to the cart |
| `PUT` | `/api/cart/update/<item_id>/` | Buyer | Update item quantity |
| `DELETE` | `/api/cart/remove/<item_id>/` | Buyer | Remove item from cart |
| `POST` | `/api/cart/clear/` | Buyer | Empty the cart |

```bash
# Add variant ID 1 to cart
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/cart/add/ \
  -H "Content-Type: application/json" \
  -d '{"variant_id": 1, "quantity": 2}'

# View cart
curl -b cookies.txt http://127.0.0.1:8000/api/cart/
```

### Orders

| Method | URL | Auth | Description |
|---|---|---|---|
| `POST` | `/orders/checkout/` | Buyer | Create order from cart |
| `GET` | `/orders/` | Buyer | List own orders (paginated) |
| `GET` | `/orders/<id>/` | Buyer | Order detail |
| `POST` | `/orders/<id>/confirm/` | Buyer | Confirm a pending order |
| `POST` | `/orders/<id>/cancel/` | Buyer | Cancel an order (within 30 min) |
| `POST` | `/orders/<order_id>/items/<item_id>/fulfil/` | Seller | Mark item as fulfilled |
| `GET` | `/orders/summary/` | Seller | Sales summary (optional `start_date`, `end_date`) |

```bash
# Checkout (converts cart to order)
curl -b cookies.txt -X POST http://127.0.0.1:8000/orders/checkout/

# List my orders
curl -b cookies.txt http://127.0.0.1:8000/orders/

# Seller sales summary for a date range
curl -b seller-cookies.txt \
  "http://127.0.0.1:8000/orders/summary/?start_date=2024-01-01&end_date=2024-12-31"
```

---

## Project Structure

```
e_commerce_platform/
├── core/                  # Base templates, home page, seed command
│   ├── templates/core/
│   └── management/commands/seed.py
├── users/                 # Registration, login, profiles, seller public page
├── products/              # Product & category models, stock service, API views
├── cart/                  # Cart model, session cart, HTML + API views
├── orders/                # Order model, checkout service, seller dashboard
├── e_comerce_platform/    # Django settings and root URL conf
├── Makefile               # Developer automation (setup, run, test, reset)
└── manage.py
```

Each app follows the same internal layout: `models.py`, `views.py`, `urls.py`, `services.py`, `admin.py`, `tests.py`. Business logic lives exclusively in `services.py` — views only handle HTTP.

---

## Known Limitations

This is a demonstration project. The following are intentional simplifications:

- **Payment is mocked** — checkout immediately creates a confirmed order with no real payment gateway
- **No email notifications** — order confirmations are shown on-screen only
- **SQLite only** — sufficient for local development; a production deployment would use PostgreSQL
- **No image uploads via API** — product images can only be set through the Django admin

---

## Running Tests

```bash
make test
```

Tests cover seller/buyer role enforcement, seller order visibility (sellers only see orders containing their own products), seller profile views, and unauthenticated access redirects.

---

## Contributors

| Contributor | Key contributions |
|---|---|
| **Jose Cleber** | Products app, Category, Product & ProductVariant models, migrations, product list/detail/category/search views, product admin, URL routing |
| **Sabrina** | Cart app (models, views, services, admin, URLs), Orders app (models, views, services, admin, URLs), cart service layer, order service layer |
| **SRamoras** | Project initialisation, Django setup, Users app, login/register/profile views, seller profile, Bootstrap 5 base template, home page, product list/detail HTML pages, seller product management, buyer/seller role restrictions, admin improvements, cart bug fixes, seed command & Makefile, product cards showing seller |
