# 📖 BookVerse — Django Microservices Bookstore

## Architecture Overview

```
bookstore/
├── docker-compose.yml          # Orchestrates all services
├── nginx/nginx.conf            # Reverse proxy config
└── services/
    ├── auth_service/           # :8001 — Auth microservice
    │   ├── accounts/           # User model, JWT, views
    │   └── auth_service/       # Django settings + URLs
    └── frontend_service/       # :8000 — Frontend
        ├── pages/              # Views (proxy → auth API)
        └── templates/          # HTML + CSS + JS
```

## API Endpoints (Auth Service)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/api/auth/register/` | No | Register (ID auto-increment, password hashed) |
| POST | `/api/auth/login/` | No | Login → JWT access + refresh tokens |
| POST | `/api/auth/logout/` | Bearer | Blacklist refresh token |
| POST | `/api/auth/token/refresh/` | No | Refresh access token |
| GET | `/api/auth/profile/` | Bearer | Get current user profile |
| PATCH | `/api/auth/profile/` | Bearer | Update profile |
| POST | `/api/auth/change-password/` | Bearer | Change password |
| GET | `/api/auth/verify/` | Bearer | Token introspection (for other services) |
| GET | `/api/auth/health/` | No | Health check |

## Quick Start

### 1. Prerequisites
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
docker --version        # Must be 24+
docker compose version  # Must be 2+
```

### 2. Clone / Download this project
```bash
cd bookstore   # This folder
```

### 3. Build & Run
```bash
docker compose up --build
```
Wait ~60s for first build. Then open:
- **Frontend**: http://localhost
- **Auth API**: http://localhost/api/auth/health/
- **Django Admin**: http://localhost/api/auth/admin/  (create superuser below)

### 4. Create Superuser (optional)
```bash
docker exec -it bookstore_auth_service python manage.py createsuperuser
```

### 5. Stop
```bash
docker compose down           # Stop (keep DB)
docker compose down -v        # Stop + delete DB volume
```

## Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character

## Test the API directly

```bash
# Register
curl -X POST http://localhost/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@bookverse.com","username":"testuser","password":"Test@1234","password2":"Test@1234"}'

# Login
curl -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@bookverse.com","password":"Test@1234"}'

# Profile (use access token from login)
curl http://localhost/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

## Services & Ports (internal)

| Service | Port |
|---------|------|
| Nginx (public) | 80 |
| Frontend Django | 8000 |
| Auth Django | 8001 |
| PostgreSQL | 5432 |
| Redis | 6379 |

