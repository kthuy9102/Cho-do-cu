# Back-end: Chợ đồ cũ sinh viên (Đề tài 4)

Phần của vai trò **Back-end**: API, nghiệp vụ, xác thực JWT + phân quyền, xử lý lỗi, logging.
Minh chứng trên GitHub: `app/routers/`, `app/security/`, `app/schemas/` (cùng `app/services/`, `app/core/`).

## 1. Cấu trúc

```
app/
├── main.py              # tạo app, middleware, CORS, đăng ký router, /health
├── config.py            # đọc .env (pydantic-settings), kiểm tra JWT_SECRET_KEY
├── routers/             # auth, users, categories, listings, offers, orders, notifications, reviews, reports, favorites, moderation
├── schemas/             # Pydantic: kiểm chứng dữ liệu vào/ra, Page[T], ErrorResponse
├── security/
│   ├── passwords.py     # Argon2id: hash/verify/rehash
│   ├── tokens.py        # tạo/giải mã JWT HS256
│   ├── dependencies.py  # get_current_user, require_roles, require_admin/moderator
│   └── throttle.py      # chặn dò mật khẩu (5 lần sai / 15 phút / (IP, email))
├── services/            # nghiệp vụ dùng chung: listings, offers/orders (transaction), notifications, uploads
├── core/                # exceptions, error_handlers, logging_config, middleware, pagination
├── models.py, database.py   # THAM KHẢO: thuộc phân hệ CSDL, thay bằng bản chính thức của nhóm
```

## 2. Chạy thử, seed, test

```bash
cp .env.example .env          # sửa DATABASE_URL, tạo JWT_SECRET_KEY bằng: openssl rand -hex 32
pip install -r requirements.txt
python -m scripts.seed --create-tables   # tạo bảng (khi dev) + nạp dữ liệu demo
uvicorn app.main:app --reload            # Swagger: http://localhost:8000/docs
```

Khi nhóm đã có Alembic: chạy migration trước rồi `python -m scripts.seed` (bỏ `--create-tables`).

**Tài khoản demo** (mật khẩu công khai, chỉ dùng demo):

| Vai trò | Email | Mật khẩu |
|---|---|---|
| admin | admin@example.com | Admin12345 |
| moderator | mod@example.com | Mod12345678 |
| student (người bán, có sẵn 4 tin) | an@example.com | Student123 |
| student (người mua) | binh@example.com | Student123 |

**Test và lint** (SQLite trong bộ nhớ, không cần Docker/PostgreSQL):

```bash
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing   # chạy toàn bộ test + đo độ phủ
ruff check app tests scripts                 # lint
```

Bộ test (`tests/`) gồm: `test_auth` (đăng ký/đăng nhập/JWT/giới hạn đăng nhập), `test_permissions` (401/403, đổi quyền có hiệu lực ngay,
quản trị), `test_listings` (đăng, duyệt, tìm kiếm, phân trang, N+1, upload ảnh), `test_offers_reviews` (đề nghị, chấp nhận, đánh giá,
báo cáo, yêu thích), `test_errors_and_logging` (định dạng lỗi, request_id, log), `test_units` (băm mật khẩu, token, tiện ích).
CI: `.github/workflows/backend-ci.yml` chạy lint + test trên mỗi Pull Request.
Test **không** kiểm được khóa dòng `FOR UPDATE` (SQLite bỏ qua); cần thử tay hoặc test riêng trên PostgreSQL.

### Postman

Thư mục `postman/` có 2 file: `chodocu.postman_collection.json` (94 request, mỗi request có test script) và `chodocu.postman_environment.json`.

1. Import cả hai vào Postman, chọn environment **Chợ đồ cũ - local**.
2. Chạy server và seed dữ liệu demo (mục trên). Nên đặt `MAX_LISTINGS_PER_DAY=50` trong `.env` khi test, vì mỗi lần chạy tạo 2 tin của người bán.
3. **Runner** → chọn collection → chạy các thư mục `00` đến `06` theo đúng thứ tự (bỏ chọn thư mục `07`). Thứ tự quan trọng vì request sau dùng biến do request trước lưu (token, id tin, id đề nghị).
4. Thư mục `07 THỦ CÔNG` cần tự chọn file ảnh (upload) và bấm Send 6 lần (giới hạn đăng nhập): chạy tay, không đưa vào Runner.

| Thư mục | Chứng minh được |
|---|---|
| 00 Hệ thống | API và CSDL hoạt động |
| 01 Xác thực | đăng ký, đăng nhập 4 vai trò, 401, không nâng quyền được qua đăng ký |
| 02 Phân quyền và danh mục | 401 so với 403, quản trị danh mục, hàng đợi kiểm duyệt |
| 03 Tin đăng và kiểm duyệt | tin chờ duyệt, duyệt, lọc/sắp xếp/phân trang, sửa tin thì duyệt lại |
| 04 Mua bán và đánh giá | đề nghị, chấp nhận (tin thành sold), đánh giá, điểm uy tín |
| 05 Báo cáo và yêu thích | báo cáo, ẩn tin vi phạm, yêu thích |
| 06 Định dạng lỗi và request_id | mọi lỗi cùng một dạng, có request_id |\n| 08 Đơn hàng và thông báo | đặt mua, xác nhận, giao, hoàn tất, đọc thông báo |

Chạy bằng dòng lệnh (dùng được trong CI nếu có server): `npx newman run postman/chodocu.postman_collection.json -e postman/chodocu.postman_environment.json`.


Container backend chạy `alembic upgrade head` trước khi khởi động API; Docker image đã đóng gói `migrations/` và `alembic.ini`. Khi chạy trực tiếp ngoài Docker, tự chạy migration trước khi bật Uvicorn.

## 2.1. Quản lý schema bằng Alembic

Alembic là nguồn quản lý phiên bản cấu trúc CSDL. Không dùng `Base.metadata.create_all()` trong quy trình triển khai production.

**CSDL mới / chưa có bảng:**

```bash
cd backend
alembic upgrade head
```

**Tạo migration sau khi thay đổi ORM model:**

```bash
cd backend
alembic revision --autogenerate -m "describe_schema_change"
alembic upgrade head
```

Luôn mở và rà soát file migration được sinh tự động trước khi chạy; autogenerate không phát hiện đầy đủ mọi thay đổi (đặc biệt rename dữ liệu/column và một số constraint).

**CSDL đã có dữ liệu từ trước:** trước khi áp dụng migration baseline, sao lưu và kiểm tra schema thực tế. Nếu schema hiện tại khớp hoàn toàn với model ở revision đầu tiên, đánh dấu baseline mà không tạo/xóa bảng:

```bash
cd backend
alembic stamp 0001_initial_schema
```

Không chạy `alembic upgrade head` trên CSDL cũ chưa được đối chiếu. Không dùng `alembic downgrade base` trên dữ liệu production vì migration đầu tiên có thao tác xóa các bảng ứng dụng.

Kiểm tra revision hiện tại:

```bash
alembic current
alembic history
```

## 3. Vai trò và ma trận phân quyền

Vai trò: `student` (vừa mua vừa bán), `moderator`, `admin` (admin có mọi quyền của moderator). Đăng ký luôn tạo `student`.

| Chức năng | Khách | student | moderator | admin |
|---|:--:|:--:|:--:|:--:|
| Xem/tìm tin đã duyệt, danh mục, hồ sơ & đánh giá người bán | ✔ | ✔ | ✔ | ✔ |
| Đăng tin, sửa/xóa tin của mình, upload ảnh | – | ✔ | ✔ | ✔ |
| Gửi/hủy đề nghị mua; chấp nhận/từ chối đề nghị trên tin của mình | – | ✔ | ✔ | ✔ |
| Đánh giá người bán, báo cáo tin, yêu thích | – | ✔ | ✔ | ✔ |
| Duyệt/từ chối tin, xử lý báo cáo, xóa tin vi phạm | – | – | ✔ | ✔ |
| Quản lý danh mục, người dùng (đổi vai trò, khóa) | – | – | – | ✔ |

Quy tắc đi kèm: không tự duyệt tin của mình; admin không tự đổi vai trò/khóa chính mình; không đặt mua/báo cáo tin của mình.

## 4. Bảng endpoint (tiền tố `/api/v1`)

| Method | Đường dẫn | Quyền | Thành công | Lỗi có thể gặp |
|---|---|---|---|---|
| POST | `/auth/register` | Khách | 201 | 409 email trùng, 422 |
| POST | `/auth/login` (form: username=email) | Khách | 200 | 401, 403 bị khóa, 429 |
| POST | `/auth/change-password` | Đăng nhập | 200 | 400, 401, 422 |
| GET / PATCH | `/users/me` | Đăng nhập | 200 | 401, 422 |
| GET | `/users` | admin | 200 | 401, 403 |
| GET | `/users/{id}` | Khách | 200 | 404 |
| PATCH | `/users/{id}/role`, `/users/{id}/active` | admin | 200 | 403, 404, 422 |
| GET | `/users/{id}/reviews` | Khách | 200 | 404 |
| GET | `/categories` | Khách | 200 | – |
| POST / PATCH / DELETE | `/categories`, `/categories/{id}` | admin | 201 / 200 / 204 | 403, 404, 409, 422 |
| GET | `/listings` (q, category_id, min_price, max_price, condition, sort, page, page_size) | Khách | 200 | 422 |
| GET | `/listings/mine` | Đăng nhập | 200 | 401 |
| POST | `/listings` | Đăng nhập | 201 | 401, 422, 429 vượt 5 tin/24h |
| GET | `/listings/{id}` | Khách (tin chưa duyệt: chủ tin/mod) | 200 | 404 |
| PATCH | `/listings/{id}` | Chủ tin | 200 | 403, 404, 409, 422 |
| DELETE | `/listings/{id}` | Chủ tin / mod | 204 | 403, 404, 409 đã bán |
| POST | `/listings/{id}/images` (multipart `files`) | Chủ tin | 201 | 409 quá 5 ảnh, 413, 415 |
| DELETE | `/listings/{id}/images/{image_id}` | Chủ tin | 204 | 403, 404, 409 |
| POST | `/listings/{id}/offers` | Đăng nhập | 201 | 403 tin của mình, 404, 409 trùng/đã bán, 422 |
| GET | `/offers/sent`, `/offers/received`, `/offers/{id}` | Người trong cuộc | 200 | 404 |
| POST | `/offers/{id}/accept`, `/reject` | Người bán | 200 | 404, 409 |
| POST | `/offers/{id}/cancel` | Người mua | 200 | 404, 409 |
| POST | `/listings/{id}/orders` | Người mua | 201 | 401, 403, 404, 409, 422 |
| GET | `/orders?side=buying|selling|all` | Người trong cuộc | 200 | 401, 422 |
| GET | `/orders/{id}` | Người mua/người bán | 200 | 401, 404 |
| POST | `/orders/{id}/confirm` | Người bán | 200 | 404, 409 |
| POST | `/orders/{id}/ship` | Người bán | 200 | 404, 409 |
| POST | `/orders/{id}/complete` | Người mua | 200 | 404, 409 |
| POST | `/orders/{id}/cancel` | Người mua/người bán, trước khi giao | 200 | 404, 409 |
| GET | `/notifications`, `/notifications/unread-count` | Chủ tài khoản | 200 | 401, 422 |
| PATCH | `/notifications/{id}/read` | Người nhận | 200 | 401, 404 |
| POST | `/notifications/read-all` | Chủ tài khoản | 204 | 401 |
| POST | `/offers/{id}/review` | Người mua (sau khi được chấp nhận) | 201 | 404, 409, 422 |
| POST | `/listings/{id}/reports` | Đăng nhập | 201 | 403, 404, 409 |
| PUT / DELETE | `/listings/{id}/favorite` | Đăng nhập | 204 | 404 |
| GET | `/favorites` | Đăng nhập | 200 | 401 |
| GET | `/moderation/listings`, `/moderation/reports` | moderator, admin | 200 | 401, 403 |
| POST | `/moderation/listings/{id}/approve`, `/reject` | moderator, admin | 200 | 403, 404, 409, 422 |
| PATCH | `/moderation/reports/{id}` | moderator, admin | 200 | 403, 404, 409 |
| GET | `/health` | Khách | 200 | 503 |

### 20 endpoint chính (dùng cho slide 7 và demo)

API đầy đủ có 50 endpoint (bảng ở trên); 20 endpoint sau là luồng nghiệp vụ chính, ứng với 20 request trong `postman/chodocu_20api.postman_collection.json`.

| # | Method | Đường dẫn | Quyền | Thành công |
|---|---|---|---|---|
| 1 | POST | `/auth/register` | Khách | 201 |
| 2 | POST | `/auth/login` | Khách | 200 |
| 3 | GET | `/users/me` | Đăng nhập | 200 |
| 4 | GET | `/categories` | Khách | 200 |
| 5 | POST | `/categories` | admin | 201 |
| 6 | POST | `/listings` | Đăng nhập | 201 |
| 7 | POST | `/moderation/listings/{id}/approve` | moderator, admin | 200 |
| 8 | GET | `/listings` (tìm kiếm, lọc, sắp xếp, phân trang) | Khách | 200 |
| 9 | GET | `/listings/{id}` | Khách | 200 |
| 10 | PATCH | `/listings/{id}` | Chủ tin | 200 |
| 11 | POST | `/moderation/listings/{id}/reject` | moderator, admin | 200 |
| 12 | DELETE | `/listings/{id}` | Chủ tin, moderator | 204 |
| 13 | POST | `/listings/{id}/offers` | Đăng nhập | 201 |
| 14 | GET | `/offers/received` | Người bán | 200 |
| 15 | POST | `/offers/{id}/accept` | Người bán | 200 |
| 16 | POST | `/offers/{id}/review` | Người mua | 201 |
| 17 | GET | `/users/{id}` (điểm uy tín) | Khách | 200 |
| 18 | POST | `/listings/{id}/reports` | Đăng nhập | 201 |
| 19 | PATCH | `/moderation/reports/{id}` | moderator, admin | 200 |
| 20 | POST | `/listings/{id}/images` (upload ảnh) | Chủ tin | 201 |

Collection 20 request chạy theo đúng thứ tự trên bằng Runner (request 20 cần chọn file ảnh nên bỏ tick khi chạy Runner). Mỗi lần chạy tạo 3 tin của người bán.
Collection chính có 94 request (`chodocu.postman_collection.json`): 82 request cũ và 12 request mới ở thư mục `08`, bao phủ luồng đơn hàng/thông báo cùng các ca lỗi 401, 403, 409, 422, 429.

## 5. Luồng JWT (slide 8)

1. `POST /auth/login` → kiểm tra mật khẩu bằng Argon2id → trả `access_token` (HS256, hạn `ACCESS_TOKEN_EXPIRE_MINUTES`).
2. Client gửi `Authorization: Bearer <token>`.
3. `get_current_user`: giải mã (cố định thuật toán, bắt buộc `exp`/`iat`/`sub`) → đọc user từ CSDL → kiểm tra `is_active`.
4. `require_roles(...)` so vai trò **đọc từ CSDL** với danh sách cho phép → sai thì 403.

Payload gồm `sub`, `iat`, `exp`, `jti`, `type`. JWT chỉ được **ký**, không **mã hóa**, nên không chứa dữ liệu nhạy cảm. Vai trò không nằm trong token nên khóa tài khoản / đổi quyền có hiệu lực ngay. Token hết hạn → 401 `token_expired`, client chuyển về trang đăng nhập.

Chống tự nâng quyền: `RegisterRequest`/`UserUpdate` không có trường `role` và dùng `extra="forbid"` (gửi thừa trường → 422); đổi vai trò chỉ qua `PATCH /users/{id}/role` của admin.

## 6. Quy ước lỗi

Mọi lỗi cùng một dạng, có `request_id` để tra log:

```json
{"error": {"code": "duplicate_offer", "message": "...", "details": null, "request_id": "9f2c..."}}
```

| Mã | Dùng khi |
|---|---|
| 400 | Yêu cầu sai nghiệp vụ đơn giản (sai mật khẩu hiện tại) |
| 401 | Thiếu/sai/hết hạn token, sai email hoặc mật khẩu |
| 403 | Đã đăng nhập nhưng không đủ quyền hoặc vi phạm quy tắc (mua tin của mình) |
| 404 | Không có, hoặc không được phép biết là có (tin chưa duyệt của người khác, đề nghị của người khác) |
| **409** | Dữ liệu **hợp lệ** nhưng **xung đột trạng thái hiện tại**: email trùng, đề nghị trùng, tin đã bán, đã đánh giá rồi |
| **422** | Dữ liệu **sai định dạng/giá trị** (Pydantic): email sai, giá âm, thiếu trường; `details` liệt kê từng trường |
| 413 / 415 | Ảnh quá lớn / không phải JPEG, PNG, WebP (kiểm cả chữ ký file, không tin `Content-Type`) |
| 429 | Đăng nhập sai quá nhiều, đăng quá 5 tin/ngày |
| 500 | Lỗi không lường trước: log đầy đủ stack trace, client chỉ thấy thông báo chung |

PATCH (không phải PUT) cho mọi cập nhật một phần: chỉ gửi trường cần đổi, xử lý bằng `model_dump(exclude_unset=True)`.
Path param xác định **tài nguyên** (`/listings/{id}`), query param **lọc/sắp xếp/phân trang** (`?q=&sort=&page=`).

## 7. Logging

JSON một dòng/sự kiện ra stdout (Docker thu được bằng `docker logs`), mỗi dòng có `request_id` (cũng trả về header `X-Request-ID`).
- `request_completed`: method, path, status_code, duration_ms, client_ip (không log query string, body, mật khẩu, token).
- Sự kiện bảo mật (`app.security`): `login_failed`, `login_success`, `permission_denied`, `role_changed`, `password_changed`.
- Sự kiện nghiệp vụ: `listing_created/approved/rejected`, `offer_accepted`, `report_resolved`...
- `LOG_LEVEL`, `LOG_JSON=false` để đọc dễ khi phát triển.

## 8. Quy tắc nghiệp vụ chính

- Tin mới ở trạng thái `pending`; khách chỉ thấy `approved`. Sửa nội dung/ảnh của tin `approved`/`rejected` → quay về `pending`.
- Chấp nhận đề nghị chạy trong **một transaction**, khóa dòng tin bằng `SELECT ... FOR UPDATE`: tin → `sold`, các đề nghị chờ khác tự bị từ chối. Hai người cùng bấm "chấp nhận" → người sau nhận 409.
- Mỗi người một đề nghị chờ cho mỗi tin; mỗi đề nghị một đánh giá (UNIQUE `offer_id`); mỗi người một báo cáo cho mỗi tin.
- Điểm uy tín = trung bình `rating` trong bảng `reviews` (`GET /users/{id}`).
- Danh sách nạp sẵn quan hệ (`joinedload`/`selectinload`) để tránh lỗi **N+1**.

## 9. Việc cần phối hợp với các thành viên khác

- **CSDL/QA**: `models.py` ở đây chỉ để tham khảo; nếu đổi tên cột/enum phải báo để sửa router. Nên thêm index duy nhất một phần (PostgreSQL) chống hai đề nghị chờ trùng khi gửi đồng thời:
  `CREATE UNIQUE INDEX uq_offers_one_pending ON offers (listing_id, buyer_id) WHERE status = 'pending';`
- **DevOps/Nginx**: chạy `uvicorn ... --proxy-headers --forwarded-allow-ips="*"` để `client_ip` (và giới hạn đăng nhập) dùng IP thật; `client_max_body_size 30m` (tối đa 5 ảnh × 5 MB); mount volume cho `UPLOAD_DIR`; ảnh phục vụ qua `/media/...`; `/health` làm healthcheck; chạy container bằng user không phải root.
- **Front-end**: gửi `Authorization: Bearer`; gặp 401 `token_expired` thì về trang đăng nhập; đọc `error.code` để hiển thị, `error.details` để tô đỏ từng ô nhập (lỗi 422).

## 10. Hạn chế đã biết (nên nêu thẳng khi vấn đáp)

- Token không thu hồi được trước khi hết hạn (chưa có refresh token/blacklist); đổi mật khẩu không vô hiệu hóa token cũ. Hướng phát triển: access token ngắn + refresh token lưu CSDL.
- `login_throttle` lưu trong bộ nhớ một tiến trình: chạy nhiều worker cần Redis.
- Tìm kiếm dùng `ILIKE %q%`: đủ cho quy mô đồ án; lớn hơn nên dùng full-text search/`pg_trgm`.
