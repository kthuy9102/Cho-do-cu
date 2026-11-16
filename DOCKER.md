# Chạy Chợ đồ cũ bằng Docker Compose

Bộ Compose gồm 3 service:

- `db`: PostgreSQL 16, dữ liệu lưu trong volume `postgres_data`.
- `backend`: FastAPI + Uvicorn, kết nối PostgreSQL qua hostname nội bộ `db`.
- `frontend`: Nginx phục vụ giao diện tĩnh và reverse proxy API/ảnh về backend.

## 1. Chuẩn bị

Yêu cầu Docker Desktop đã bật Linux containers / Linux engine và Docker Compose v2.

Mở PowerShell tại thư mục gốc repository:

```powershell
Copy-Item .env.example .env
```

Mở file `.env`, thay hai giá trị:

- `POSTGRES_PASSWORD`: mật khẩu PostgreSQL đủ mạnh.
- `JWT_SECRET_KEY`: tạo bằng lệnh `python -c "import secrets; print(secrets.token_hex(32))"` rồi dán kết quả vào file.

Không commit file `.env` lên Git.

## 2. Build và chạy

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

Chờ service `db` healthy và backend chạy xong. Sau đó tạo bảng và dữ liệu demo lần đầu:

```powershell
docker compose exec backend python -m scripts.seed --create-tables
```

Lệnh seed chỉ tạo dữ liệu demo nếu database chưa có user. Không chạy `--create-tables` như cơ chế migration lâu dài; giai đoạn SQL tiếp theo sẽ bổ sung Alembic.

## 3. Kiểm tra

- Giao diện: http://localhost:8080
- Swagger: http://localhost:8080/docs
- OpenAPI: http://localhost:8080/openapi.json
- Health API + DB: http://localhost:8080/health
- PostgreSQL từ máy host: `localhost:5433` (user/database lấy trong file `.env`).

Tài khoản demo:

| Vai trò | Email | Mật khẩu |
|---|---|---|
| admin | admin@example.com | Admin12345 |
| moderator | mod@example.com | Mod12345678 |
| student | an@example.com | Student123 |
| student | binh@example.com | Student123 |

Chỉ dùng tài khoản/mật khẩu demo trong môi trường local.

## 4. Lệnh quản trị

```powershell
docker compose logs -f backend
docker compose logs -f db
docker compose restart backend
docker compose down
```

Dừng container nhưng giữ dữ liệu: `docker compose down`.

XÓA CẢ DỮ LIỆU PostgreSQL và ảnh đã upload (không thể khôi phục nếu không có backup):

```powershell
docker compose down -v
```

## 5. Ghi chú PostgreSQL đang có trên máy

Compose chạy PostgreSQL riêng trong container và publish ra host ở cổng `5433`, không chiếm cổng `5432` của PostgreSQL cài sẵn trên Windows. Backend trong Docker phải dùng hostname `db`, không dùng `localhost` để kết nối service database.

Nếu muốn dùng dữ liệu từ PostgreSQL cài sẵn trên Windows thay vì DB container, cần cấu hình network/host riêng; không đổi URL thành `localhost` bên trong container.
