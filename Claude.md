# CLAUDE.md — djangodemostore

This file is the authoritative instruction set for Claude Code when working on this project.
Read it in full before taking any action. Follow every constraint exactly as written.
When in doubt, ask rather than assume.

---

## 1. Project Overview

**djangodemostore** is a demonstration e-commerce platform built with Django 6.
It is not a production system. Payment processing is mocked. Download delivery for digital
products is not implemented. The goal is a clean, well-structured codebase that demonstrates
correct Django patterns at every layer.

---

## 2. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Web framework | Django 6 | Use async views only where explicitly instructed |
| Language | Python 3.12+ | Type hints encouraged but not mandatory |
| Database | PostgreSQL 16 | Via psycopg3 (`psycopg[binary]`) |
| Cache / Sessions | Redis 7 | django-redis backend |
| Partial API | Django REST Framework | Cart and Search endpoints only |
| Task queue | Celery + Redis broker | Scaffolded only -- no actual tasks |
| Frontend | Django Templates + HTMX | No React, no Vue, no iframes |
| Containerisation | Docker Compose | Three services only (see Section 9) |
| Media storage | Local filesystem | `MEDIA_ROOT` = `/app/media/` inside container |
| Search | PostgreSQL full-text search | `django.contrib.postgres` -- no external engine |

---

## 3. Repository Structure

Create exactly this layout. Do not add extra top-level directories without instruction.

```
djangodemostore/
├── CLAUDE.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
├── config/                        # Django project package (replaces default project name)
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py          # Stubbed, not wired up
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── __init__.py
│   ├── store/                     # Landing, Search, Product pages
│   ├── users/                     # Login, Register, Profile, Order History
│   └── orders/                    # Cart, Confirmation, Success
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── base.html
│   ├── partials/
│   ├── store/
│   ├── users/
│   └── orders/
├── media/                         # Gitignored -- created at runtime
└── celery_app/
    ├── __init__.py
    └── tasks/
        └── __init__.py            # Empty -- scaffold only
```

---

## 4. Django Apps

Each app lives under `apps/`. Register them in `INSTALLED_APPS` as `apps.store`, `apps.users`,
`apps.orders`. Each app must have its own `urls.py`, `models.py`, `views.py`, `serializers.py`
(only where DRF is used), `forms.py`, `admin.py`, and `apps.py`.

### 4.1 apps.store

**Purpose:** Public-facing storefront.

**URLs:**

| Name | Path | View | Notes |
|---|---|---|---|
| `store:landing` | `/` | `LandingPageView` | CBV, ListView of featured products |
| `store:search` | `/search/` | `SearchView` | DRF `APIView`, returns JSON |
| `store:product` | `/product/<slug:slug>/` | `ProductDetailView` | CBV, DetailView |
| `store:category` | `/category/<slug:slug>/` | `CategoryView` | CBV, ListView filtered by category |

**Models:** None -- store views read from shared models in `apps.orders` and a dedicated
`catalogue` module (see Section 5).

### 4.2 apps.users

**Purpose:** Authentication and user profile management.

**URLs:**

| Name | Path | View | Notes |
|---|---|---|---|
| `users:login` | `/accounts/login/` | `LoginView` | Override Django's built-in |
| `users:logout` | `/accounts/logout/` | `LogoutView` | POST only |
| `users:register` | `/accounts/register/` | `RegisterView` | CBV, CreateView |
| `users:profile` | `/accounts/profile/` | `ProfileView` | Login required, CBV |
| `users:order_history` | `/accounts/orders/` | `OrderHistoryView` | Login required, ListView |

**Models:**

- `UserProfile` -- OneToOne with `django.contrib.auth.models.User`. Fields: `phone`,
  `default_shipping_address` (FK to `Address`).
- `Address` -- Fields: `user` (FK, nullable for guests), `full_name`, `line1`, `line2`,
  `city`, `postcode`, `country` (CharField, ISO 3166-1 alpha-2), `is_default` (bool).

### 4.3 apps.orders

**Purpose:** Cart management and order lifecycle.

**URLs:**

| Name | Path | View | Notes |
|---|---|---|---|
| `orders:cart` | `/cart/` | `CartView` | Template view reads from Redis |
| `orders:cart_add` | `/cart/add/` | `CartAddView` | DRF `APIView`, POST only |
| `orders:cart_remove` | `/cart/remove/` | `CartRemoveView` | DRF `APIView`, POST only |
| `orders:cart_update` | `/cart/update/` | `CartUpdateView` | DRF `APIView`, POST only |
| `orders:checkout` | `/checkout/` | `CheckoutView` | Login or guest session required |
| `orders:confirm` | `/checkout/confirm/` | `OrderConfirmView` | POST, transitions order to paid |
| `orders:success` | `/checkout/success/<uuid:order_id>/` | `OrderSuccessView` | GET |

---

## 5. Data Models

Define all catalogue-related models in `apps/store/models.py`.
Define all order-related models in `apps/orders/models.py`.
Define all user-related models in `apps/users/models.py`.

### 5.1 Catalogue Models (apps/store/models.py)

#### Category

```
id              -- AutoField PK
name            -- CharField(max_length=200)
slug            -- SlugField(unique=True)
parent          -- FK('self', null=True, blank=True, related_name='children')
description     -- TextField(blank=True)
created_at      -- DateTimeField(auto_now_add=True)
```

Rules:
- Maximum nesting depth is two levels (parent and child only). Do not enforce in DB --
  enforce in the `clean()` method.
- `__str__` returns full path: `"Electronics > Phones"` if child, `"Electronics"` if root.

#### ProductType

```
id              -- AutoField PK
name            -- CharField(max_length=100, choices=[('physical', 'Physical'), ('digital', 'Digital')])
```

This is a choice field, not a separate model. Use `TextChoices`.

#### Product

```
id              -- AutoField PK
name            -- CharField(max_length=300)
slug            -- SlugField(unique=True)
description     -- TextField
product_type    -- CharField(max_length=20, choices=ProductType.choices)
category        -- FK(Category, on_delete=PROTECT)
base_price      -- DecimalField(max_digits=10, decimal_places=2)
image           -- ImageField(upload_to='products/', blank=True, null=True)
search_vector   -- SearchVectorField(null=True, blank=True)  -- from django.contrib.postgres
is_active       -- BooleanField(default=True)
created_at      -- DateTimeField(auto_now_add=True)
updated_at      -- DateTimeField(auto_now=True)
```

Rules:
- `search_vector` is populated via a `post_save` signal using `SearchVector('name', weight='A')`
  combined with `SearchVector('description', weight='B')`.
- Add a `GinIndex` on `search_vector` in `Meta.indexes`.
- `base_price` is the fallback price when no variants exist. If variants exist, treat
  `base_price` as display-only (the lowest variant price is shown on listing pages).

#### ProductVariant

```
id              -- AutoField PK
product         -- FK(Product, on_delete=CASCADE, related_name='variants')
sku             -- CharField(max_length=100, unique=True)
name            -- CharField(max_length=200)  -- e.g. "Red / XL"
price           -- DecimalField(max_digits=10, decimal_places=2)
stock           -- PositiveIntegerField(default=0)
is_active       -- BooleanField(default=True)
```

Rules:
- Physical products may have zero or more variants.
- Digital products must have exactly one variant with `stock=0` (stock is meaningless
  for digital; use the variant row for price only). Enforce in `clean()`.

### 5.2 Order Models (apps/orders/models.py)

#### OrderStatus (TextChoices)

```python
class OrderStatus(models.TextChoices):
    PENDING       = 'pending',       'Pending'
    PAID          = 'paid',          'Paid'
    PROCESSING    = 'processing',    'Processing'
    SHIPPED       = 'shipped',       'Shipped'
    DELIVERED     = 'delivered',     'Delivered'
    CANCELLED     = 'cancelled',     'Cancelled'
    REFUNDED      = 'refunded',      'Refunded'
```

#### Order

```
id              -- UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
user            -- FK(User, null=True, blank=True, on_delete=SET_NULL)  -- null = guest
guest_email     -- EmailField(blank=True)
status          -- CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
shipping_address-- FK(Address, null=True, blank=True, on_delete=SET_NULL)
total_price     -- DecimalField(max_digits=10, decimal_places=2)
created_at      -- DateTimeField(auto_now_add=True)
updated_at      -- DateTimeField(auto_now=True)
```

Rules:
- Either `user` or `guest_email` must be set. Enforce in `clean()`.
- `total_price` is computed and stored at order creation time from the cart snapshot.
  Never recalculate from line items after creation.
- Valid status transitions (enforce in a `transition_status()` model method, not in the view):
  - `pending` -> `paid`
  - `paid` -> `processing`
  - `processing` -> `shipped`
  - `shipped` -> `delivered`
  - `paid` -> `cancelled`
  - `pending` -> `cancelled`
  - `paid` -> `refunded`
  - `delivered` -> `refunded`
  - All other transitions must raise `ValueError`.

#### OrderItem

```
id              -- AutoField PK
order           -- FK(Order, on_delete=CASCADE, related_name='items')
variant         -- FK(ProductVariant, on_delete=PROTECT)
quantity        -- PositiveIntegerField()
unit_price      -- DecimalField(max_digits=10, decimal_places=2)  -- snapshot at order time
```

Rules:
- `unit_price` is written once at order creation. Never update it.
- `line_total` is a property: `return self.unit_price * self.quantity`.

---

## 6. Redis / Cart Architecture

### Session Configuration

```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'djangodemostore',
    }
}

SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days
SESSION_SAVE_EVERY_REQUEST = False
```

### Cart Data Structure

The cart is stored in the session under the key `'cart'`. Its structure is:

```python
{
    "<variant_id: int>": {
        "quantity": int,
        "price_snapshot": str,   # Decimal serialised as string, e.g. "29.99"
        "product_name": str,
        "variant_name": str,
        "product_slug": str,
        "image_url": str | None
    }
}
```

Rules:
- `price_snapshot` is set at add-to-cart time from `ProductVariant.price`. It is never
  updated even if the variant price changes later.
- Cart keys are variant IDs cast to strings (JSON does not allow integer keys).
- If a variant is added that already exists in the cart, increment `quantity` only.
- When quantity reaches zero, remove the key entirely.
- The cart helper must be a class `Cart` in `apps/orders/cart.py` with the following
  public interface:

```python
class Cart:
    def __init__(self, request): ...
    def add(self, variant: ProductVariant, quantity: int = 1) -> None: ...
    def remove(self, variant_id: int) -> None: ...
    def update(self, variant_id: int, quantity: int) -> None: ...
    def clear(self) -> None: ...
    def __iter__(self): ...          # yields enriched cart item dicts
    def __len__(self): ...           # total item count (sum of quantities)
    @property
    def total_price(self) -> Decimal: ...
```

---

## 7. Search

Use `django.contrib.postgres.search`. The search endpoint is a DRF `APIView` at `/search/`.

### Request

```
GET /search/?q=<query>&category=<slug>&type=<physical|digital>&page=<n>
```

### Implementation

```python
from django.contrib.postgres.search import SearchQuery, SearchRank

queryset = (
    Product.objects
    .filter(is_active=True)
    .annotate(rank=SearchRank('search_vector', SearchQuery(q)))
    .filter(rank__gte=0.1)
    .order_by('-rank')
    .select_related('category')
    .prefetch_related('variants')
)
```

Apply `category` and `type` filters after the rank annotation if provided.
Paginate with DRF's `PageNumberPagination`, page size 24.

### Response Shape

```json
{
  "count": 120,
  "next": "/search/?q=shoes&page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Running Shoes",
      "slug": "running-shoes",
      "product_type": "physical",
      "base_price": "49.99",
      "image_url": "/media/products/shoes.jpg",
      "category": {
        "name": "Footwear",
        "slug": "footwear"
      }
    }
  ]
}
```

---

## 8. Authentication and Guest Checkout

- Use Django's built-in `django.contrib.auth` entirely.
- `LoginView` redirects to `store:landing` on success.
- `RegisterView` creates `User` + `UserProfile` in a single transaction using
  `transaction.atomic()`.
- For guest checkout: the guest's email is collected on the checkout form and stored on
  `Order.guest_email`. The cart lives in their session regardless of auth state.
- `@login_required` is applied only to `ProfileView` and `OrderHistoryView`.
- All other views must work for both authenticated and anonymous users.

---

## 9. Docker Compose

Three services: `web`, `db`, `redis`. No nginx, no Celery worker, no Mailhog.

```yaml
# docker-compose.yml -- exact service names must match these
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - media_data:/app/media
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: djangodemostore
      POSTGRES_USER: djangodemostore
      POSTGRES_PASSWORD: djangodemostore

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
  media_data:
```

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

---

## 10. Settings Architecture

Use split settings: `config/settings/base.py`, `config/settings/development.py`.
The `DJANGO_SETTINGS_MODULE` env var selects the active settings file.
Default in `.env.example`: `config.settings.development`.

Use `django-environ` (`environ`) for all environment variable parsing.

### Required .env variables

```
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=change-me
DEBUG=True
DATABASE_URL=postgres://djangodemostore:djangodemostore@db:5432/djangodemostore
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
MEDIA_ROOT=/app/media
```

---

## 11. Requirements

Pin all versions. The `requirements.txt` must include at minimum:

```
Django>=6.0,<7.0
psycopg[binary]>=3.1
django-redis>=5.4
djangorestframework>=3.15
django-environ>=0.11
Pillow>=10.0          # ImageField support
celery>=5.3           # Scaffolded only
```

---

## 12. Celery Scaffold

Create `celery_app/__init__.py` with a configured Celery app instance pointing to the
`config` Django settings module. Create `celery_app/tasks/__init__.py` as an empty file
with a comment: `# Tasks will be registered here`. Do not implement any tasks.
Do not start a Celery worker service in Docker Compose.

In `config/settings/base.py`:

```python
CELERY_BROKER_URL = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_TASK_ALWAYS_EAGER = True   # In dev: tasks run synchronously and inline
```

---

## 13. Admin Registration

Every model must be registered in its app's `admin.py`. Use `@admin.register` decorator.
Apply the following as a minimum:

- `Product`: `list_display = ['name', 'product_type', 'category', 'is_active']`,
  `prepopulated_fields = {'slug': ('name',)}`, `search_fields = ['name']`
- `ProductVariant`: inline on Product admin using `TabularInline`
- `Category`: `list_display = ['name', 'parent']`, `prepopulated_fields = {'slug': ('name',)}`
- `Order`: `list_display = ['id', 'status', 'user', 'guest_email', 'total_price', 'created_at']`,
  `readonly_fields = ['id', 'total_price', 'created_at']`
- `OrderItem`: inline on Order admin using `TabularInline`, all fields `readonly`

---

## 14. URL Structure

`config/urls.py` must include:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.store.urls', namespace='store')),
    path('accounts/', include('apps.users.urls', namespace='users')),
    path('cart/', include('apps.orders.urls', namespace='orders')),
    path('api/', include([
        path('search/', include('apps.store.api_urls')),
        path('cart/', include('apps.orders.api_urls')),
    ])),
]
```

Separate `urls.py` (template views) from `api_urls.py` (DRF views) within each app.

---

## 15. Frontend Conventions

- Base template: `templates/base.html`. All other templates extend it.
- HTMX is loaded via CDN in `base.html`. Pin the version: `htmx.org@1.9.12`.
- Cart add/remove/update interactions use HTMX `hx-post` targeting a `#cart-summary`
  partial that re-renders the cart count in the navbar.
- No custom JavaScript files are required at project init. Add only if explicitly instructed.
- Static files: CSS in `static/css/main.css`. No CSS framework is prescribed -- use
  plain CSS or add one only if explicitly instructed.

---

## 16. MCP Server Setup

Claude Code should attempt to bootstrap a local MCP server for documentation lookup.
Use the **MCP Python SDK** (`mcp` package from PyPI).

Create `mcp_server/` at the repository root with the following structure:

```
mcp_server/
├── __init__.py
├── server.py          # Entry point
├── tools/
│   ├── __init__.py
│   ├── django_docs.py
│   ├── postgres_docs.py
│   └── redis_docs.py
└── requirements.txt   # Separate from main app requirements
```

### MCP server requirements

```
mcp>=1.0
httpx>=0.27
beautifulsoup4>=4.12
```

### Tools to expose

Each tool fetches live documentation from official sources via `httpx` and returns
the relevant section as plain text.

| Tool name | Source URL base | Purpose |
|---|---|---|
| `django_docs_search` | `https://docs.djangoproject.com/en/6.0/` | Query Django 6 docs |
| `postgres_docs_search` | `https://www.postgresql.org/docs/16/` | Query PostgreSQL 16 docs |
| `redis_docs_search` | `https://redis.io/docs/latest/` | Query Redis docs |

Each tool takes a single `query: str` argument. Implementation should:
1. Construct a search URL or fetch a known documentation page relevant to the query.
2. Parse the HTML with BeautifulSoup, extract the main content text.
3. Return a trimmed string of the most relevant section (max 2000 characters).

### MCP server entry point

```python
# mcp_server/server.py
from mcp.server.fastmcp import FastMCP
from mcp_server.tools.django_docs import django_docs_search
from mcp_server.tools.postgres_docs import postgres_docs_search
from mcp_server.tools.redis_docs import redis_docs_search

mcp = FastMCP("djangodemostore-docs")
mcp.tool()(django_docs_search)
mcp.tool()(postgres_docs_search)
mcp.tool()(redis_docs_search)

if __name__ == "__main__":
    mcp.run()
```

Register the MCP server in Claude Code's `.mcp.json` at the repository root:

```json
{
  "mcpServers": {
    "djangodemostore-docs": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "."
    }
  }
}
```

---

## 17. Execution Order

When bootstrapping the project from scratch, follow this order exactly:

1. Create the repository folder `djangodemostore/`.
2. Create `.env.example`, `.gitignore`, `requirements.txt`, `mcp_server/requirements.txt`.
3. Create `Dockerfile` and `docker-compose.yml`.
4. Create `config/` package with split settings. Wire `DATABASE_URL`, `REDIS_URL`,
   `CACHES`, `SESSION_ENGINE`, `INSTALLED_APPS`, `MEDIA_ROOT`, `STATIC_ROOT`.
5. Create `apps/store/`, `apps/users/`, `apps/orders/` -- each as a full Django app package.
6. Define all models (Section 5). Run `makemigrations` for all three apps.
7. Create `apps/store/models.py` signal for `search_vector` population.
8. Create `apps/orders/cart.py` with the `Cart` class (Section 6).
9. Create all URL files (`urls.py` and `api_urls.py`) per app.
10. Create all views (template views first, then DRF API views).
11. Create all forms (`forms.py` per app).
12. Register all models in `admin.py` per app.
13. Create `templates/base.html` and all sub-templates (empty blocks are fine).
14. Create `celery_app/` scaffold.
15. Create `mcp_server/` and implement the three doc tools.
16. Create `.mcp.json`.
17. Verify: `docker compose up --build` completes without errors.
18. Verify: `python manage.py migrate` inside the container applies all migrations cleanly.
19. Verify: `python manage.py createsuperuser` works and the admin lists all models.

---

## 18. Constraints and Non-Goals

- Do NOT install or use: `django-oscar`, `django-shop`, `saleor`, or any other
  pre-built e-commerce framework.
- Do NOT use `django-allauth` -- built-in auth only.
- Do NOT add a Nginx service to Docker Compose.
- Do NOT implement real payment processing of any kind.
- Do NOT implement digital product download delivery.
- Do NOT add a Celery worker Docker service.
- Do NOT use `sqlite3` -- PostgreSQL only, even in development.
- Do NOT generate front-end JavaScript files beyond what HTMX handles declaratively.
- All money values are stored as `DecimalField`, never `FloatField`.
- All primary keys on `Order` are UUID. All other PKs are standard auto-increment integers.
- Never commit `.env` -- only `.env.example`.
