# URL Shortener API

A production-ready URL shortener built with **FastAPI**, **PostgreSQL**, **Docker**, and **GitHub Actions CI/CD**.

## Features

- ✅ FastAPI with async SQLAlchemy 2.0
- ✅ JWT Authentication (register/login/me)
- ✅ URL shortening with custom codes
- ✅ Click tracking & expiration
- ✅ Docker multi-stage builds (dev + prod)
- ✅ PostgreSQL + Redis ready
- ✅ Pytest with async support
- ✅ Ruff linting + MyPy type checking
- ✅ GitHub Actions CI/CD pipeline

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Development

```bash
# Clone and enter
cd url-shortener

# Start all services (API + PostgreSQL + Redis)
docker compose up --build

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL & Redis (via Docker)
docker compose up -d db redis

# Run migrations (when Alembic is added)
# alembic upgrade head

# Start API with hot reload
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Get current user |

### URLs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/urls` | Create short URL |
| GET | `/urls` | List user's URLs |
| GET | `/urls/{short_code}` | Get URL info |
| DELETE | `/urls/{url_id}` | Delete URL |
| GET | `/{short_code}/redirect` | Redirect to original |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | Root endpoint |

## Example Usage

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Create short URL (use token from login)
curl -X POST http://localhost:8000/urls \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://very-long-url.example.com/path"}'

# Redirect
curl -I http://localhost:8000/abc123/redirect
```

## Project Structure

```
url-shortener/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # Async SQLAlchemy
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT + password hashing
│   ├── dependencies.py      # FastAPI dependencies
│   ├── routers/
│   │   ├── auth.py          # Auth endpoints
│   │   └── urls.py          # URL endpoints
│   └── services/
│       └── url_service.py   # Business logic
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_health.py
│   ├── test_auth.py
│   └── test_urls.py
├── .github/workflows/ci.yml # CI/CD pipeline
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Dev services
├── pyproject.toml           # Project config
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/url_shortener` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `SECRET_KEY` | `change-me-in-production` | JWT secret (CHANGE IN PROD!) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiry |
| `ENVIRONMENT` | `development` | `development` or `production` |

## Testing

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_auth.py -v

# Run with Docker (integration style)
docker compose run --rm app pytest
```

## Linting & Type Checking

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy app
```

## Deployment

### Production Build

```bash
# Build production image
docker build --target production -t url-shortener:latest .

# Run with production settings
docker run -d \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  -e SECRET_KEY=super-secret-key \
  -e ENVIRONMENT=production \
  -p 8000:8000 \
  url-shortener:latest
```

### Kubernetes (Helm)

Coming in Week 10-12 of the learning plan.

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR:

1. **Lint** - Ruff + MyPy
2. **Test** - Pytest with PostgreSQL service
3. **Docker** - Build & push to GHCR (main branch only)

## Next Steps (Learning Plan)

- [ ] Add Alembic migrations
- [ ] Add Redis caching for redirects
- [ ] Add rate limiting
- [ ] Add OpenTelemetry observability
- [ ] Kubernetes deployment with Helm
- [ ] GitOps with ArgoCD

## License

MIT