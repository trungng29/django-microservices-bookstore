# 🔧 Debug Guide

## Nếu gặp 502 Bad Gateway

### Bước 1: Xem logs từng service
```bash
# Xem tất cả logs
docker compose logs -f

# Xem riêng từng service
docker compose logs auth_service
docker compose logs frontend_service
docker compose logs nginx
docker compose logs auth_db
```

### Bước 2: Kiểm tra container có đang chạy không
```bash
docker compose ps
```
Tất cả phải có status = "Up". Nếu "Exit" thì xem logs.

### Bước 3: Test kết nối trực tiếp (bypass nginx)
```bash
# Test auth service trực tiếp
curl http://localhost:8001/api/auth/health/

# Test frontend trực tiếp  
curl http://localhost:8000/
```

### Bước 4: Rebuild sạch hoàn toàn
```bash
docker compose down -v          # Xóa containers + volumes
docker compose build --no-cache # Rebuild không dùng cache
docker compose up               # Chạy lại
```

### Lỗi thường gặp:
| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| 502 ngay sau start | Services chưa kịp khởi động | Chờ 30s rồi refresh |
| auth_service Exit | PostgreSQL chưa ready | Tự động retry, chờ thêm |
| 500 Internal Error | Xem `docker compose logs auth_service` | |
| Static files 404 | Chạy `collectstatic` | Tự động trong Dockerfile |
