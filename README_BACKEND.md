# Back-end: Chợ đồ cũ sinh viên (Đề tài 4)

Phần của vai trò **Back-end**: API, nghiệp vụ, xác thực JWT + phân quyền, xử lý lỗi, logging.
Minh chứng trên GitHub: `app/routers/`, `app/security/`, `app/schemas/` (cùng `app/services/`, `app/core/`).

## 1. Cấu trúc

```
app/
├── main.py              # tạo app, middleware, CORS, đăng ký router, /health
├── config.py            # đọc .env (pydantic-settings), kiểm tra JWT_SECRET_KEY
├── routers/             # auth, users, categories, listings, offers, reviews, reports, favorites, moderation
├── schemas/             # Pydantic: kiểm chứng dữ liệu vào/ra, Page[T], ErrorResponse
├── security/
│   ├── passwords.py     # Argon2id: hash/verify/rehash
│   ├── tokens.py        # tạo/giải mã JWT HS256
│   ├── dependencies.py  # get_current_user, require_roles, require_admin/moderator
│   └── throttle.py      # chặn dò mật khẩu (5 lần sai / 15 phút / (IP, email))
├── services/            # nghiệp vụ dùng chung: listings, offers (transaction), uploads
├── core/                # exceptions, error_handlers, logging_config, middleware, pagination
├── models.py, database.py   # THAM KHẢO: thuộc phân hệ CSDL, thay bằng bản chính thức của nhóm
```

## 2. Chạy thử

```bash
cp .env.example .env          # sửa DATABASE_URL, tạo JWT_SECRET_KEY bằng: openssl rand -hex 32
pip install -r requirements.txt
uvicorn app.main:app --reload # Swagger: http://localhost:8000/docs
```
Tạo bảng/seed do phân hệ CSDL làm (Alembic). Cần seed ít nhất: 1 `admin`, 1 `moderator`, vài `student`, vài danh mục.

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
| POST | `/offers/{id}/review` | Người mua (sau khi được chấp nhận) | 201 | 404, 409, 422 |
| POST | `/listings/{id}/reports` | Đăng nhập | 201 | 403, 404, 409 |
| PUT / DELETE | `/listings/{id}/favorite` | Đăng nhập | 204 | 404 |
| GET | `/favorites` | Đăng nhập | 200 | 401 |
| GET | `/moderation/listings`, `/moderation/reports` | moderator, admin | 200 | 401, 403 |
| POST | `/moderation/listings/{id}/approve`, `/reject` | moderator, admin | 200 | 403, 404, 409, 422 |
| PATCH | `/moderation/reports/{id}` | moderator, admin | 200 | 403, 404, 409 |
| GET | `/health` | Khách | 200 | 503 |

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
