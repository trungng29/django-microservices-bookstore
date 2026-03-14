# 📖 BookVerse — Django Microservices Bookstore

## Kiến trúc tổng quan

```
bookstore/
├── docker-compose.yml
├── nginx/
└── services/
    ├── auth_service        :8001  ← Đăng ký, đăng nhập, RBAC
    ├── catalog_service     :8002  ← Sách, tác giả, danh mục
    ├── shop_service        :8003  ← Gian hàng người bán
    ├── order_service       :8004  ← Đơn hàng, giỏ hàng, thanh toán
    ├── interaction_service :8005  ← Đánh giá, wishlist, coupon
    └── frontend_service    :8000  ← UI (proxy tới các API)
```

Nginx (port 80) là entry point duy nhất, route request tới đúng service.

---

## 🚀 Khởi động nhanh

```bash
# Lần đầu: build toàn bộ
docker compose up --build

# Từ lần sau:
docker compose up

# Rebuild 1 service:
docker compose up --build auth_service
```

Truy cập: **http://localhost**

---

## 👥 Hệ thống phân quyền (RBAC)

### 4 Roles

| Role | Mô tả | Đăng ký |
|------|-------|---------|
| `customer` | Khách hàng mua sách | Tự đăng ký |
| `seller`   | Nhà sách / người bán | Tự đăng ký → admin duyệt KYC |
| `author`   | Tác giả sách | Tự đăng ký → admin xác minh |
| `admin`    | Quản trị viên | `createsuperuser` |

### Đăng ký theo role

```bash
# Đăng ký khách hàng (mặc định)
POST /api/auth/register/
{ "email": "...", "username": "...", "password": "...", "password2": "...", "role": "customer" }

# Đăng ký người bán
{ ..., "role": "seller" }

# Đăng ký tác giả
{ ..., "role": "author" }
```

### Quyền theo role (tóm tắt)

| | Customer | Seller | Author | Admin |
|---|:---:|:---:|:---:|:---:|
| Xem sách/catalogue | ✅ | ✅ | ✅ | ✅ |
| Đăng/sửa/xoá sách | ❌ | ✅ (shop mình) | ❌ | ✅ (tất cả) |
| Tạo/sửa tác giả | ❌ | ✅ (tạo) | ✅ (sửa của mình) | ✅ |
| Tạo/quản lý shop | ❌ | ✅ | ❌ | ✅ |
| Đặt hàng | ✅ | ✅ | ✅ | ✅ |
| Xem đơn shop | ❌ | ✅ (shop mình) | ❌ | ✅ (tất cả) |
| Viết đánh giá | ✅ | ✅ | ✅ | ✅ |
| Moderate | ❌ | ❌ | ❌ | ✅ |
| Gán/thu hồi role | ❌ | ❌ | ❌ | ✅ |

---

## 📡 API Reference

### Auth Service (`/api/auth/`)

| Method | Endpoint | Auth | Role | Mô tả |
|--------|----------|------|------|-------|
| POST | `register/` | No | — | Đăng ký tài khoản |
| POST | `login/` | No | — | Đăng nhập → JWT |
| POST | `logout/` | Bearer | All | Đăng xuất |
| POST | `token/refresh/` | No | — | Refresh access token |
| GET | `profile/` | Bearer | All | Xem profile |
| PATCH | `profile/` | Bearer | All | Sửa profile |
| POST | `change-password/` | Bearer | All | Đổi mật khẩu |
| GET | `seller-profile/` | Bearer | seller | Xem seller profile |
| PATCH | `seller-profile/` | Bearer | seller | Cập nhật seller profile |
| GET | `author-profile/` | Bearer | author | Xem author profile |
| PATCH | `author-profile/` | Bearer | author | Cập nhật author profile |
| POST | `roles/assign/` | Bearer | admin | Gán role cho user |
| POST | `roles/revoke/` | Bearer | admin | Thu hồi role |
| GET | `verify/` | Bearer | All | Verify token (service-to-service) |
| GET | `health/` | No | — | Health check |

### Catalog Service (`/api/catalog/`)

| Method | Endpoint | Auth | Role | Mô tả |
|--------|----------|------|------|-------|
| GET | `books/` | No | — | Danh sách sách (filter/search/sort) |
| GET | `books/<slug>/` | No | — | Chi tiết sách |
| POST | `books/upload/` | Bearer | seller | **Đăng sách mới** |
| PATCH | `books/<id>/manage/` | Bearer | seller/admin | Sửa sách |
| DELETE | `books/<id>/manage/` | Bearer | seller/admin | Xoá sách |
| POST | `books/<id>/publish/` | Bearer | admin | Duyệt sách |
| GET | `authors/` | No | — | Danh sách tác giả |
| POST | `authors/` | Bearer | seller/admin | Tạo tác giả |
| GET | `authors/<id>/` | No | — | Chi tiết tác giả |
| PATCH | `authors/<id>/` | Bearer | author/admin | Sửa tác giả |
| GET | `categories/` | No | — | Cây danh mục |
| GET | `publishers/` | No | — | Danh sách NXB |
| POST | `publishers/` | Bearer | seller/admin | Tạo NXB |

#### Query params `/api/catalog/books/`
```
q           Tìm theo tên/tác giả/ISBN
category    Slug danh mục
author      Slug tác giả
shop_id     ID gian hàng
language    vi | en | ja | zh | ko
format      paperback | hardcover | ebook | audiobook
featured    1
bestseller  1
ordering    -created_at | -avg_rating | -total_sold
page        Số trang (20 sách/trang)
```

#### Upload sách — ví dụ cURL
```bash
# Seller đăng nhập trước để lấy access token
TOKEN="Bearer eyJ..."

# Tạo tác giả
curl -X POST http://localhost/api/catalog/authors/ \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Nguyễn Nhật Ánh", "nationality": "Vietnam"}'
# → { "id": 1, "name": "Nguyễn Nhật Ánh", ... }

# Upload sách (multipart với ảnh bìa)
curl -X POST http://localhost/api/catalog/books/upload/ \
  -H "Authorization: $TOKEN" \
  -F "title=Tôi thấy hoa vàng trên cỏ xanh" \
  -F "description=Cuốn tiểu thuyết..." \
  -F "author_ids=1" \
  -F "category_ids=2" \
  -F "original_price=120000" \
  -F "sale_price=95000" \
  -F "language=vi" \
  -F "book_format=paperback" \
  -F "stock_quantity=100" \
  -F "shop_id=1" \
  -F "cover_image=@cover.jpg"
```

---

## 🖥️ Frontend Pages

| URL | Mô tả | Role |
|-----|-------|------|
| `/` | Trang chủ — featured + bestseller | Public |
| `/catalogue/` | Danh sách sách — filter, search, sort | Public |
| `/books/<slug>/` | Chi tiết sách | Public |
| `/seller/upload/` | Form đăng sách mới | seller, admin |
| `/register/` | Đăng ký tài khoản | Public |
| `/login/` | Đăng nhập | Public |
| `/profile/` | Trang cá nhân | All |

---

## 🔧 Lệnh hữu ích

```bash
# Tạo superuser (admin)
docker compose exec auth_service python manage.py createsuperuser

# Seed roles & permissions
docker compose exec auth_service python manage.py seed_permissions

# Xem logs real-time
docker compose logs -f auth_service
docker compose logs -f catalog_service

# Truy cập Django shell
docker compose exec catalog_service python manage.py shell

# Rebuild sạch hoàn toàn
docker compose down -v
docker compose build --no-cache
docker compose up
```

---

## 🗄️ Cơ sở dữ liệu

| Service | DB | Port (internal) |
|---------|-----|-----------------|
| auth_service | auth_db (PostgreSQL) | 5432 |
| catalog_service | catalog_db (PostgreSQL) | 5432 |
| shop_service | shop_db (PostgreSQL) | 5432 |
| order_service | order_db (PostgreSQL) | 5432 |
| interaction_service | interaction_db (PostgreSQL) | 5432 |
| frontend_service | SQLite (sessions only) | — |

Mỗi service có **database riêng biệt** — không JOIN trực tiếp cross-service.
Giao tiếp giữa services qua HTTP REST API.

---

## 🔐 JWT Token Structure

```json
{
  "user_id": 1,
  "username": "seller_nguyen",
  "email": "nguyen@shop.vn",
  "roles": ["seller"],
  "primary_role": "seller",
  "permissions": [
    "catalog:book:create",
    "catalog:book:update_own",
    "catalog:author:create",
    "shop:shop:create",
    ...
  ],
  "is_verified": true,
  "exp": 1234567890
}
```

Các microservice đọc JWT trực tiếp — **không cần gọi lại auth_service** mỗi request.

---

## 📁 Password Requirements

- Tối thiểu 8 ký tự
- Ít nhất 1 chữ HOA (A-Z)
- Ít nhất 1 chữ số (0-9)
- Ít nhất 1 ký tự đặc biệt (!@#$...)
