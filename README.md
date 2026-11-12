# Publisher Entitlements

A Django REST Framework API for a publisher's Entitlement Service. The API
grants and revokes products and returns a user's current entitlements.

Users hold subscriptions to products (Digital, Print, Premium), and each
product grants a set of benefits (web access, print magazine, ad-free).

User -> Subscription -> Product -> Benefit

## Requirements

- Python 3.12+

## Setup

```bash
git clone https://github.com/ysmilde/publisher-entitlements.git
cd publisher-entitlements

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # the placeholder values work for local use
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

The API is now running at http://127.0.0.1:8000

## Demo data

`seed_data` creates the benefits, products, users and subscriptions below. It is safe to
run more than once.

Only `admin` can log in. The other users just hold subscriptions.

| ID | User | Subscriptions | Entitlements |
|---|---|---|---|
| 1 | `maia` | Premium, active | web access, print magazine, ad-free |
| 2 | `monty` | Digital (expired), then Print (active) | web access, print magazine |
| 3 | `momo` | Digital, revoked | none |
| 4 | `admin` | none (superuser) | none |

Product IDs: Digital `1`, Print `2`, Premium `3`.

## API

All endpoints require a login. In the browser, log in at
http://127.0.0.1:8000/api-auth/login/ as `admin` / `admin123`.

| Method | URL | Body |
|---|---|---|
| POST | `/api/subscriptions/` | `{"user_id": 3, "product_id": 1}` grants a product |
| POST | `/api/subscriptions/revoke/` | `{"user_id": 3, "product_id": 1}` revokes it |
| GET | `/api/users/<user_id>/entitlements/` | returns the user's benefits |

Each URL opens in DRF's browsable API, where you can submit requests from a form. For
example, http://127.0.0.1:8000/api/users/1/entitlements/ shows maia's benefits.

The admin site is at http://127.0.0.1:8000/admin/ (log in as `admin`).

## Running tests

```bash
python manage.py test
```

## Resetting the data

Delete `db.sqlite3`, then run `python manage.py migrate` and `python manage.py seed_data`
again.
