# e-Commerce Platform

A demonstration e-commerce web application built with Django. It supports two user roles — **Buyers** and **Sellers** — each with their own dedicated workflows, from browsing and purchasing products to listing and managing orders.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
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
Authenticated endpoints require a logged-in session (or session cookie).

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

### Cart

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/cart/` | Buyer | View current cart |
| `POST` | `/api/cart/add/` | Buyer | Add a variant to the cart |
| `PUT` | `/api/cart/update/<item_id>/` | Buyer | Update item quantity |
| `DELETE` | `/api/cart/remove/<item_id>/` | Buyer | Remove item from cart |
| `POST` | `/api/cart/clear/` | Buyer | Empty the cart |

### Orders

| Method | URL | Auth | Description |
|---|---|---|---|
| `POST` | `/orders/checkout/` | Buyer | Create order from cart |
| `GET` | `/orders/` | Buyer | List own orders (paginated) |
| `GET` | `/orders/<id>/` | Buyer | Order detail |
| `POST` | `/orders/<id>/confirm/` | Buyer | Confirm a pending order |
| `POST` | `/orders/<id>/cancel/` | Buyer | Cancel an order |
| `POST` | `/orders/<order_id>/items/<item_id>/fulfil/` | Seller | Mark item as fulfilled |
| `GET` | `/orders/summary/` | Seller | Sales summary (optional `start_date`, `end_date`) |

---

## Running Tests

```bash
make test
```

Tests cover user registration and roles, product creation and stock changes, cart operations, order lifecycle and status transitions, and seller-specific views.

---

## Contributors

| Contributor | Key contributions |
|---|---|
| **corujitoo / Jose Cleber** | Project initialisation, Django setup, Products app, Category & Product models, stock services, search signal |
| **Sabrina** | Cart and Orders apps, cart/checkout logic, URL wiring |
| **SRamoras** | Users app, login/register/profile views, seller profile, Bootstrap 5 base template, home page, product list/detail HTML pages, seller product management, buyer/seller role restrictions, admin improvements, cart bug fixes, seed command & Makefile, product cards showing seller |
