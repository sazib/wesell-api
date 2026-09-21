# WeSell API — Bakery & Cake Shop Backend

A Django REST Framework API for an online bakery store (cakes, cupcakes, cookies, custom cakes). It powers a storefront frontend with product catalog, cart, checkout, payment gateway integration, reviews, and countdown offers.

## Features

- **Authentication & accounts** — register, login (email or username), profile/dashboard, password reset via OTP, password history tracking. Custom `CustomUser` model with phone, address, city, and WhatsApp number.
- **Catalog** — categories, products with sizes (`small`–`12"`, by weight), flavors, sale prices, image galleries, featured/advanced-order flags, and per-product stock. Delivery areas with configurable delivery fees.
- **Search & nav** — search endpoint and navigation (nav) endpoint for the storefront.
- **Cart** — anonymous or user-scoped cart service with add/update/clear/count endpoints.
- **Orders** — checkout, order creation, cancellation, payment confirmation, plus **custom cake** orders (with a meta endpoint exposing available options/sizes/flavors/pricing).
- **Payments** — pluggable gateway that supports **Razorpay, Stripe, and SSLCommerz** (sandbox mode by default).
- **Reviews** — per-product reviews.
- **Offers** — countdown offers/promotions.
- **Admin** — full Django admin for managing all entities.
- **Seed command** — generates a demo dataset with placeholder cake images.

## Tech Stack

- Django + Django REST Framework
- django-filter (filtering), Token & Session authentication
- Pillow (image fields), WhiteNoise (static), Gunicorn
- PostgreSQL via `dj-database-url` (SQLite by default in development)
- Optional Redis cache via `REDIS_URL`
- SMTP email (falls back to console backend in development)

## Project Structure

```
api/        core settings, URL routing, exception handler
accounts/   custom user, auth, OTP password reset
catalog/    categories, products, delivery areas, search, seed command
cart/       cart & cart item models + service layer
orders/     orders, order items, custom-cake orders, payment gateway
reviews/    product reviews
offers/     countdown offers
```

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. (Optional) Seed demo data
python manage.py seed

# 5. Create a superuser for the admin
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver
```

The API will be available at <http://127.0.0.1:8000/> and the admin at <http://127.0.0.1:8000/admin/>.

## Configuration

All configuration is driven by environment variables (see `api/settings.py`):

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key | dev key (do not use in prod) |
| `DJANGO_DEBUG` | Debug mode (`true`/`false`) | `true` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | `127.0.0.1,localhost` |
| `DATABASE_URL` | Database connection string | SQLite (`db.sqlite3`) |
| `REDIS_URL` | Optional Redis cache location | off |
| `PAYMENT_GATEWAY` | `razorpay` / `stripe` / `sslcommerz` | `sandbox` |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Razorpay credentials | empty |
| `STRIPE_PUBLISHABLE_KEY` / `STRIPE_SECRET_KEY` | Stripe credentials | empty |
| `SSLCOMMERZ_STORE_ID` / `SSLCOMMERZ_STORE_PASS` | SSLCommerz credentials | empty |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP settings | console backend |
| `DEFAULT_FROM_EMAIL` | Sender email address | bakery default |
| `WHATSAPP_NUMBER` / `MESSENGER_PAGE_URL` | Support contact links | empty |
| `PUBLIC_BASE_URL` | Public base URL for absolute links | request host |

## API Overview

All endpoints are under the `api/` prefix.

### Auth (`api/auth/`)
- `POST register/` — create an account
- `POST login/` — email/username login
- `POST logout/`
- `GET profile/`, `GET dashboard/`
- `POST password-reset/request/` → `POST password-reset/verify/` → `POST password-reset/confirm/` — OTP-based reset
- `POST /api/token/` — DRF auth token (TokenAuthentication)

### Catalog (`api/`)
- `GET home/` — homepage data
- `GET nav/` — navigation data
- `GET search/?q=...`
- `GET products/`, `GET products/<slug>/`
- `GET categories/`, `GET categories/<slug>/`
- `GET delivery-areas/`

### Cart (`api/cart/`)
- `GET /` — cart detail
- `POST items/` — add item
- `PUT/DELETE items/<item_id>/` — update/remove item
- `POST clear/`, `GET count/`

### Orders (`api/orders/`)
- `POST checkout/` — checkout blueprint
- `GET custom-cake/meta/` — custom cake options (sizes/flavors/pricing)
- `POST custom-cake/` — place a custom cake order
- `POST create/` — create order from cart
- `GET /` — list orders, `GET <order_number>/` — order detail
- `POST <order_number>/cancel/` — cancel
- `POST <order_number>/payment/confirm/` — confirm payment

### Reviews (`api/reviews/`)
- `POST /` — add a review

### Offers (`api/offers/`)
- `GET /` — list offers, `GET <slug>/` — offer detail

## Deployment

The repo includes a `Procfile` for Heroku-style platforms:

```
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn api.wsgi --bind 0.0.0.0:$PORT
```

Set the environment variables above (especially `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and `DJANGO_ALLOWED_HOSTS`), then deploy.