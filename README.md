# Chợ đồ cũ sinh viên

Ứng dụng web trao đổi và mua bán đồ cũ dành cho sinh viên. Hệ thống gồm giao diện web, REST API và PostgreSQL; hỗ trợ đăng tin, tìm kiếm, gửi đề nghị mua, đặt hàng, đánh giá, yêu thích và kiểm duyệt nội dung.

> Hướng dẫn này bám theo cấu hình hiện tại của repository. Cách khuyến nghị để chạy toàn bộ hệ thống là **Docker Compose**.

## 1. Chức năng chính

- Đăng ký, đăng nhập và xác thực bằng JWT.
- Phân quyền sinh viên (student), kiểm duyệt viên (moderator) và quản trị viên (admin).
- Đăng tin, tải ảnh, chỉnh sửa và quản lý tin cá nhân.
- Tìm kiếm, lọc và phân trang danh sách sản phẩm.
- Yêu thích tin đăng, gửi đề nghị mua và quản lý đơn hàng.
- Đánh giá người bán, báo cáo tin vi phạm.
- Kiểm duyệt tin đăng, xử lý báo cáo và quản lý tài khoản.
- Lưu dữ liệu nghiệp vụ và thông báo trong PostgreSQL.

## 2. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL 16 |
| Database migration | Alembic |
| Authentication | JWT (HS256), Argon2id |
| Web server / Reverse proxy | Nginx |
| Container | Docker, Docker Compose |
| Kiểm thử | pytest, Ruff, Node.js, Postman/Newman |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) |

## 3. Yêu cầu môi trường

### Chạy bằng Docker (khuyến nghị)

- Git.
- Docker Desktop có hỗ trợ Docker Compose v2.
- Docker Desktop đang chạy ở chế độ **Linux containers**.

Không cần cài Python, PostgreSQL hoặc Node.js để khởi chạy toàn bộ ứng dụng bằng Docker.

### Chạy Backend trực tiếp để phát triển

- Python 3.12.
- PostgreSQL 16 (cài trên máy hoặc chạy riêng bằng Docker).
- Git.
- Node.js 22 trở lên nếu muốn chạy kiểm thử Frontend.

## 4. Tải mã nguồn

Mở PowerShell hoặc Terminal:

~~~powershell
git clone https://github.com/kthuy9102/Cho-do-cu.git
cd Cho-do-cu
~~~

Nếu muốn lấy nhánh tích hợp đang phát triển:

~~~powershell
git switch feature/frontend-backend-integration
git pull origin feature/frontend-backend-integration
~~~

Cấu trúc chính:

~~~text
Cho-do-cu/
├── .github/workflows/       # GitHub Actions CI/CD
├── backend/
│   ├── app/                 # FastAPI application
│   ├── migrations/          # Alembic migrations
│   ├── postman/             # Postman collection/environment
│   ├── scripts/             # Seed dữ liệu demo
│   ├── tests/               # Backend tests
│   ├── .env.example         # Mẫu cấu hình Backend riêng
│   └── requirements.txt
├── deploy/
│   └── nginx.conf           # Nginx reverse proxy
├── frontend/                # Giao diện web
├── .env.example             # Mẫu cấu hình Docker Compose
├── docker-compose.yml
├── DOCKER.md
└── README.md
~~~

## 5. Cấu hình biến môi trường

Repository có **hai file mẫu .env.example cho hai cách chạy khác nhau**. Chọn đúng cách đang sử dụng.

### 5.1. Cấu hình khi chạy Docker Compose

Tại thư mục gốc repository, tạo file .env:

~~~powershell
Copy-Item .env.example .env
~~~

Tạo chuỗi mật khẩu và JWT secret ngẫu nhiên bằng Python. Chạy lệnh hai lần để có hai chuỗi riêng:

~~~powershell
python -c "import secrets; print(secrets.token_hex(32))"
~~~

Mở file .env và thay các giá trị:

~~~dotenv
POSTGRES_DB=chodocu
POSTGRES_USER=chodocu
POSTGRES_PASSWORD=THAY_BANG_MAT_KHAU_NGAU_NHIEN
JWT_SECRET_KEY=THAY_BANG_JWT_SECRET_NGAU_NHIEN
~~~

| Biến | Ý nghĩa | Giá trị mẫu |
|---|---|---|
| POSTGRES_DB | Tên database PostgreSQL | chodocu |
| POSTGRES_USER | Tài khoản database | chodocu |
| POSTGRES_PASSWORD | Mật khẩu database | Tự tạo chuỗi ngẫu nhiên |
| JWT_SECRET_KEY | Khóa bí mật dùng ký JWT | Chuỗi ngẫu nhiên tối thiểu 32 ký tự |

Docker Compose lấy các biến này từ file .env ở thư mục gốc. Các thiết lập Backend như DATABASE_URL, UPLOAD_DIR, CORS_ORIGINS và giới hạn upload được khai báo trong docker-compose.yml. Khi chạy theo cách này không cần tạo thêm backend/.env.

**Lưu ý bảo mật:**
- Không sử dụng mật khẩu hoặc JWT secret mẫu khi triển khai thật.
- Không đưa file .env lên GitHub hoặc chia sẻ công khai.
- Không dùng lại mật khẩu demo trong môi trường production.
- Nên sử dụng chuỗi hex do lệnh trên tạo ra để tránh lỗi ký tự đặc biệt khi Docker Compose đọc file .env.

### 5.2. Cấu hình khi chạy Backend trực tiếp

Chỉ thực hiện phần này nếu không chạy Backend bằng Docker. Mở thư mục Backend:

~~~powershell
cd backend
Copy-Item .env.example .env
~~~

Chỉnh file backend/.env:

~~~dotenv
ENVIRONMENT=development
DATABASE_URL=postgresql+psycopg://chodocu:MAT_KHAU@localhost:5433/chodocu

JWT_SECRET_KEY=THAY_BANG_CHUOI_NGAU_NHIEN_TREN_32_KY_TU
ACCESS_TOKEN_EXPIRE_MINUTES=60

UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=5
MAX_IMAGES_PER_LISTING=5
MAX_LISTINGS_PER_DAY=5

CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

LOG_LEVEL=INFO
LOG_JSON=true
~~~

Giải thích các biến quan trọng:

| Biến | Ý nghĩa |
|---|---|
| ENVIRONMENT | Môi trường chạy ứng dụng, ví dụ development |
| DATABASE_URL | Chuỗi kết nối PostgreSQL |
| JWT_SECRET_KEY | Khóa ký và xác minh JWT, tối thiểu 32 ký tự |
| ACCESS_TOKEN_EXPIRE_MINUTES | Thời gian hiệu lực access token (phút) |
| UPLOAD_DIR | Thư mục lưu ảnh tải lên |
| MAX_UPLOAD_SIZE_MB | Dung lượng tối đa của mỗi ảnh (MB) |
| MAX_IMAGES_PER_LISTING | Số ảnh tối đa cho một tin đăng |
| MAX_LISTINGS_PER_DAY | Số tin đăng tối đa trong ngày theo giới hạn ứng dụng |
| CORS_ORIGINS | Danh sách origin được phép gọi API, định dạng JSON |
| LOG_LEVEL | Mức độ ghi log |
| LOG_JSON | Ghi log dạng JSON nếu bật |

**Cấu hình database trong DATABASE_URL:**
- Nếu dùng PostgreSQL do Docker Compose của dự án khởi chạy, Backend chạy trực tiếp trên Windows kết nối qua localhost:5433.
- Nếu PostgreSQL được cài trực tiếp trên Windows và lắng nghe cổng mặc định, dùng localhost:5432.
- Nếu Backend cũng chạy trong Docker Compose, hostname database phải là db, không phải localhost.

Tạo JWT secret bằng lệnh:

~~~powershell
python -c "import secrets; print(secrets.token_hex(32))"
~~~

Thay kết quả vào JWT_SECRET_KEY. Không dùng giá trị replace-with... trong file mẫu.

## 6. Cài đặt và chạy toàn bộ hệ thống bằng Docker

Đảm bảo Docker Desktop đang chạy. Thực hiện tại **thư mục gốc** của repository.

### Bước 1. Kiểm tra cấu hình Docker Compose

~~~powershell
docker compose config
~~~

Nếu lệnh báo thiếu POSTGRES_PASSWORD hoặc JWT_SECRET_KEY, kiểm tra lại file .env ở thư mục gốc.

### Bước 2. Build image và khởi chạy các service

~~~powershell
docker compose up -d --build
~~~

Lệnh này khởi chạy ba service:

| Service | Chức năng |
|---|---|
| db | PostgreSQL 16 |
| backend | FastAPI, tự chạy Alembic migration trước khi bật API |
| frontend | Nginx phục vụ giao diện và chuyển tiếp request API/ảnh đến Backend |

### Bước 3. Kiểm tra trạng thái container

~~~powershell
docker compose ps
~~~

Chờ database và Backend ở trạng thái healthy. Có thể xem log:

~~~powershell
docker compose logs -f db
docker compose logs -f backend
docker compose logs -f frontend
~~~

Nhấn Ctrl + C để thoát theo dõi log; thao tác này không dừng container.

### Bước 4. Khởi tạo dữ liệu demo

Chạy một lần trên database mới:

~~~powershell
docker compose exec backend python -m scripts.seed
~~~

Lệnh seed tạo tài khoản, danh mục và dữ liệu demo. Nếu database đã có người dùng, script sẽ bỏ qua để tránh nạp trùng.

**Không thêm tham số --create-tables khi chạy theo Docker.** Cấu trúc database được quản lý bằng Alembic và Backend đã tự chạy migration khi khởi động.

### Bước 5. Truy cập ứng dụng

| Thành phần | Địa chỉ |
|---|---|
| Website | http://localhost:8080 |
| Swagger UI | http://localhost:8080/docs |
| OpenAPI JSON | http://localhost:8080/openapi.json |
| Health check | http://localhost:8080/health |
| PostgreSQL từ máy host | localhost:5433 |

Nếu trang web không truy cập được, kiểm tra Docker Desktop và trạng thái các container bằng docker compose ps.

## 7. Chạy Backend trực tiếp (không chạy Backend trong Docker)

Cách này dành cho phát triển hoặc debug API. Cần có PostgreSQL đang chạy và file backend/.env đã cấu hình đúng ở mục 5.2.

### Bước 1. Tạo môi trường Python ảo

Tại thư mục gốc:

~~~powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
~~~

Nếu PowerShell chặn việc kích hoạt môi trường ảo, chạy:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
~~~

### Bước 2. Cài thư viện

~~~powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

### Bước 3. Chạy database migration

Đảm bảo PostgreSQL đã hoạt động và DATABASE_URL trong backend/.env trỏ đến database đó:

~~~powershell
alembic upgrade head
~~~

Alembic tạo/cập nhật các bảng theo phiên bản migration của dự án.

### Bước 4. Nạp dữ liệu demo

~~~powershell
python -m scripts.seed
~~~

### Bước 5. Khởi động API

~~~powershell
uvicorn app.main:app --reload
~~~

Backend chạy tại http://localhost:8000. Tài liệu API:
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health check: http://localhost:8000/health

Khi hoàn tất, dừng server bằng Ctrl + C và thoát môi trường ảo:

~~~powershell
deactivate
~~~

> Nếu chạy Frontend qua Docker/Nginx, cấu hình proxy phải trỏ đúng địa chỉ Backend. Cách đơn giản nhất để chạy giao diện và API đồng bộ là sử dụng Docker Compose ở mục 6.

## 8. Tài khoản demo

Sau khi chạy seed thành công, có thể đăng nhập bằng các tài khoản:

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Admin | admin@example.com | Admin12345 |
| Moderator | mod@example.com | Mod12345678 |
| Sinh viên | an@example.com | Student123 |
| Sinh viên | binh@example.com | Student123 |

Các tài khoản trên chỉ phục vụ học tập, demo và kiểm thử local. Không sử dụng trong môi trường triển khai thật.

## 9. Kiểm thử

### 9.1. Backend: pytest và Ruff

Tại thư mục gốc:

~~~powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

ruff check app tests scripts
pytest --cov=app --cov-report=term-missing
~~~

### 9.2. Frontend: kiểm tra cú pháp và smoke tests

Cần Node.js 22 trở lên. Chạy tại thư mục gốc:

~~~powershell
node --check frontend\app.js
node --test frontend/tests/*.test.js
~~~

### 9.3. Kiểm thử API bằng Postman

Các file kiểm thử nằm trong backend/postman/:

- chodocu.postman_collection.json: Postman collection.
- chodocu.postman_environment.json: Environment cho local.

Các bước:

1. Khởi chạy hệ thống và seed dữ liệu demo theo mục 6.
2. Mở Postman, Import cả collection và environment.
3. Chọn environment **Chợ đồ cũ - local**.
4. Kiểm tra biến base_url đang trỏ đến http://localhost:8080 nếu chạy qua Docker; nếu chạy Backend trực tiếp thì đổi thành http://localhost:8000.
5. Mở Collection Runner và chạy các thư mục theo thứ tự 00 đến 06, sau đó 08.
6. Thư mục 07 THỦ CÔNG chứa các request cần thao tác thủ công (ví dụ chọn file ảnh); thực hiện riêng theo hướng dẫn trong collection.

Các nhóm kiểm thử bao gồm hệ thống/health, xác thực, phân quyền, danh mục, tin đăng, kiểm duyệt, mua bán, đánh giá, báo cáo, yêu thích, định dạng lỗi, đơn hàng và thông báo.

Có thể chạy các nhóm tự động bằng Newman từ thư mục gốc (cần Node.js/npm):

~~~powershell
npx --yes newman run backend/postman/chodocu.postman_collection.json `
  --environment backend/postman/chodocu.postman_environment.json `
  --env-var "base_url=http://localhost:8080" `
  --folder "00 Hệ thống" `
  --folder "01 Xác thực" `
  --folder "02 Phân quyền và danh mục" `
  --folder "03 Tin đăng và kiểm duyệt" `
  --folder "04 Mua bán và đánh giá" `
  --folder "05 Báo cáo và yêu thích" `
  --folder "06 Định dạng lỗi và request_id" `
  --folder "08 Đơn hàng và thông báo"
~~~

Một số request tạo dữ liệu mới; nên dùng database local dành riêng cho kiểm thử.

## 10. CI/CD bằng GitHub Actions

Workflow được khai báo tại .github/workflows/backend-ci.yml.

Khi push code hoặc tạo Pull Request, GitHub Actions thực hiện:

1. **Backend:** cài dependencies, chạy Ruff và pytest.
2. **Frontend:** kiểm tra cú pháp JavaScript và chạy smoke tests.
3. **Docker integration:** build và khởi chạy toàn bộ stack, kiểm tra health/API, seed dữ liệu CI và chạy Postman/Newman.
4. **Publish image:** khi push lên nhánh main và các job kiểm thử cần thiết thành công, workflow build và publish Backend/Frontend images lên GitHub Container Registry (GHCR).

Xem kết quả tại tab Actions của repository:  
https://github.com/kthuy9102/Cho-do-cu/actions

Lưu ý: CI kiểm tra build và tích hợp trong môi trường runner. Publish image lên GHCR không đồng nghĩa ứng dụng đã được triển khai lên một máy chủ production.

## 11. Các lệnh Docker thường dùng

Chạy tại thư mục gốc:

~~~powershell
# Xem trạng thái service
docker compose ps

# Theo dõi log
docker compose logs -f backend

# Xem log database
docker compose logs -f db

# Khởi động lại Backend
docker compose restart backend

# Dừng các container, giữ dữ liệu
docker compose down

# Build lại và chạy
docker compose up -d --build
~~~

**Xóa dữ liệu:** lệnh sau xóa cả các Docker volume, bao gồm database và ảnh upload:

~~~powershell
docker compose down -v
~~~

Chỉ chạy lệnh này khi thực sự muốn xóa dữ liệu local. Không sử dụng nếu còn cần dữ liệu hoặc chưa sao lưu.

## 12. Xử lý lỗi thường gặp

| Hiện tượng | Nguyên nhân / cách xử lý |
|---|---|
| Thiếu POSTGRES_PASSWORD hoặc JWT_SECRET_KEY | Tạo file .env ở thư mục gốc từ .env.example, điền đủ giá trị rồi chạy lại Compose. |
| JWT_SECRET_KEY không hợp lệ | Tạo khóa ngẫu nhiên tối thiểu 32 ký tự; không dùng chuỗi replace-with... |
| Backend không kết nối được PostgreSQL | Kiểm tra service db, mật khẩu, database và DATABASE_URL. Trong Docker dùng hostname db; Backend chạy trên Windows dùng localhost và cổng host 5433 nếu kết nối DB của Compose. |
| Cổng 8080 đã được sử dụng | Dừng ứng dụng đang chiếm cổng hoặc đổi port publish của service frontend trong docker-compose.yml. |
| Cổng 5433 đã được sử dụng | Dừng tiến trình đang chiếm cổng hoặc đổi port host của service db; cập nhật DATABASE_URL nếu Backend chạy ngoài Docker. |
| Website/API chưa sẵn sàng ngay sau khi chạy | Đợi healthcheck hoàn tất, kiểm tra bằng docker compose ps và xem docker compose logs -f backend. |
| Swagger trả lỗi hoặc không mở được | Kiểm tra Backend có healthy không và truy cập đúng /docs qua địa chỉ frontend hoặc backend. |
| Seed không tạo lại dữ liệu | Script seed bỏ qua khi database đã có người dùng. Nếu cần môi trường sạch, sao lưu trước rồi chủ động tạo lại database/volume. |
| Lỗi migration | Kiểm tra DATABASE_URL, log Backend và trạng thái migration. Không tự ý xóa bảng hoặc chạy downgrade trên dữ liệu cần giữ. |
| Không tải được ảnh | Kiểm tra định dạng/dung lượng ảnh, quyền ghi thư mục upload và log Backend. |

## 13. Tài liệu tham khảo trong repository

- [DOCKER.md](DOCKER.md) — hướng dẫn Docker Compose chi tiết.
- [Backend README](backend/README_BACKEND.md) — cấu trúc Backend, API, phân quyền, migration và Postman.
- [GitHub Actions](.github/workflows/backend-ci.yml) — quy trình CI/CD.
- [GitHub Repository](https://github.com/kthuy9102/Cho-do-cu)

---

**Dự án phục vụ mục đích học tập và thực hành xây dựng ứng dụng web/API.** Trước khi triển khai công khai, cần thay toàn bộ secret và mật khẩu demo, rà soát cấu hình bảo mật, sao lưu database và thiết lập môi trường production riêng.
