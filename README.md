# Payment API

A robust payment processing API built with Django, Django REST Framework, Celery, Redis, and PostgreSQL.

## Setup

1. Clone repo
```bash
git clone <repo-url>
cd payment-app
```

2. Copy .env.example to .env
```bash
cp .env.example .env
```

3. Run with Docker
```bash
docker-compose up --build
```

4. Access: http://localhost:8000

## API Documentation

### Authentication

**Register:**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "merchant@example.com", "password": "pass123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "merchant@example.com", "password": "pass123"}'
```

### Transactions

**Create Payment:**
```bash
curl -X POST http://localhost:8000/api/transactions/pay/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": "100.00", "currency": "USD", "description": "Order #123"}'
```

**List Transactions:**
```bash
curl http://localhost:8000/api/transactions/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Get Transaction:**
```bash
curl http://localhost:8000/api/transactions/{id}/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### Refunds

**Create Refund:**
```bash
curl -X POST http://localhost:8000/api/refunds/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transaction": "uuid", "amount": "50.00", "reason": "Customer request"}'
```

### Webhooks

**Register Webhook:**
```bash
curl -X POST http://localhost:8000/api/webhooks/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/webhook"}'
```

**List Webhooks:**
```bash
curl http://localhost:8000/api/webhooks/list/ \
  -H "Authorization: Token YOUR_TOKEN"
```

## Testing

```bash
docker-compose exec web python manage.py test
```

## Design Decisions

- **UUID Primary Keys**: Enhanced security, prevents ID enumeration
- **Async Processing**: Celery handles transaction processing (3-5 sec delay)
- **Webhook Retries**: Automatic retry mechanism (max 3 attempts)
- **Standard Response Format**: Consistent API responses
- **Token Auth**: Secure authentication with DRF tokens

## Tech Stack

- Django 5.2.8 LTS
- Django REST Framework 3.16.1
- Celery 5.5.3
- PostgreSQL 17
- Redis 7.4
- Docker

Built with Claude Code
