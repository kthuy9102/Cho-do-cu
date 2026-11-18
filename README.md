# Chợ đồ cũ sinh viên

Ứng dụng web trao đổi và mua bán đồ cũ dành cho sinh viên. Dự án gồm giao diện web, REST API và PostgreSQL; chạy toàn bộ bằng Docker Compose.

## Chức năng chính

- Đăng ký, đăng nhập và phân quyền sinh viên, kiểm duyệt viên, quản trị viên.
- Đăng tin, tải ảnh, tìm kiếm/lọc sản phẩm và quản lý tin cá nhân.
- Gửi đề nghị mua, đặt hàng, xác nhận/giao/hoàn tất hoặc hủy đơn.
- Yêu thích sản phẩm, đánh giá người bán và gửi báo cáo vi phạm.
- Quản trị viên/kiểm duyệt viên duyệt tin và xử lý báo cáo.
- Thông báo được lưu trong PostgreSQL.

## Công nghệ

- Frontend: HTML, CSS, JavaScript.
- Backend: Python, FastAPI, SQLAlchemy, JWT.
- Database: PostgreSQL 16, quản lý schema bằng Alembic.
- Triển khai local: Docker Compose, Nginx reverse proxy.
- Kiểm thử: pytest, Ruff, Node.js smoke tests, Postman/Newman.

## Chạy nhanh trên Windows

Yêu cầu: Docker Desktop dùng Linux containers và Docker Compose v2.

1. Mở PowerShell tại thư mục gốc repo.
2. Tạo file cấu hình:

   ```powershell
   Copy-Item .env.example .env
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Mở `.env`, thay `POSTGRES_PASSWORD` bằng mật khẩu mạnh và `JWT_SECRET_KEY` bằng chuỗi vừa tạo.
4. Build và chạy:

   ```powershell
   docker compose config
   docker compose up -d --build
   docker compose ps
   ```

   Backend tự chạy `alembic upgrade head` trước khi khởi động API.

5. Nạp dữ liệu demo lần đầu:

   ```powershell
   docker compose exec backend python -m scripts.seed
   ```

   Lệnh seed bỏ qua nếu database đã có người dùng. Không thêm `--create-tables` khi dùng Docker; schema do Alembic quản lý.

## Địa chỉ truy cập

| Thành phần | Địa chỉ |
|---|---|
| Giao diện | http://localhost:8080 |
| Swagger API | http://localhost:8080/docs |
| OpenAPI JSON | http://localhost:8080/openapi.json |
| Health (API + database) | http://localhost:8080/health |
| PostgreSQL từ Windows | localhost:5433 |

## Tài khoản demo

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Admin | admin@example.com | Admin12345 |
| Moderator | mod@example.com | Mod12345678 |
| Sinh viên | an@example.com | Student123 |
| Sinh viên | binh@example.com | Student123 |

**Chỉ dùng tài khoản demo ở môi trường local.** Không sử dụng các mật khẩu này khi triển khai thật.

## Kiểm thử

Kiểm thử Backend (PowerShell, cần Python 3.12):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
ruff check app tests scripts
pytest --cov=app --cov-report=term-missing
deactivate
cd ..
```

Kiểm thử Frontend (cần Node.js 22, chạy tại thư mục gốc):

```powershell
node --check frontend\app.js
node --test frontend/tests/*.test.js
```

Chạy bộ Postman/Newman theo hướng dẫn trong [backend/README_BACKEND.md](backend/README_BACKEND.md#postman). CI trên GitHub Actions tự chạy lint, pytest, Frontend smoke tests, Docker integration và Postman/Newman.

## Lệnh Docker thường dùng

```powershell
docker compose ps
docker compose logs -f backend
docker compose logs -f db
docker compose restart backend
docker compose down
```

`docker compose down` giữ nguyên dữ liệu. **Không chạy `docker compose down -v` nếu chưa muốn xóa toàn bộ database và ảnh upload.**

Xem thêm [DOCKER.md](DOCKER.md) để biết chi tiết cấu hình và vận hành.
