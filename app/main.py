import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.database import get_db
from app.routers import auth, categories, favorites, listings, moderation, offers, reports, reviews, users

settings = get_settings()
setup_logging(settings.log_level, settings.log_json)
logger = logging.getLogger("app")

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

TAGS = [
    {"name": "Auth", "description": "Đăng ký, đăng nhập (JWT), đổi mật khẩu"},
    {"name": "Users", "description": "Hồ sơ cá nhân; quản trị người dùng (admin)"},
    {"name": "Categories", "description": "Danh mục sản phẩm"},
    {"name": "Listings", "description": "Tin đăng: tìm kiếm, lọc, phân trang, upload ảnh"},
    {"name": "Offers", "description": "Đề nghị mua và chấp nhận/từ chối"},
    {"name": "Reviews", "description": "Đánh giá người bán sau giao dịch"},
    {"name": "Reports", "description": "Báo cáo tin vi phạm"},
    {"name": "Favorites", "description": "Danh sách yêu thích"},
    {"name": "Moderation", "description": "Kiểm duyệt tin và xử lý báo cáo (moderator/admin)"},
    {"name": "System", "description": "Kiểm tra tình trạng hệ thống"},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("app_startup", extra={"environment": settings.environment})
    yield
    logger.info("app_shutdown")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "API chợ đồ cũ cho sinh viên. Xác thực bằng JWT: gọi `POST /auth/login`, "
        "rồi bấm **Authorize** và dán access token. Mọi lỗi trả về dạng "
        "`{\"error\": {\"code\", \"message\", \"details\", \"request_id\"}}`."
    ),
    openapi_tags=TAGS,
    lifespan=lifespan,
)

# Middleware thêm sau nằm ngoài cùng: CORS ngoài cùng để cả response lỗi cũng có header CORS
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,  # JWT gửi qua header Authorization, không dùng cookie
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

register_exception_handlers(app)

for module in (auth, users, categories, listings, offers, reviews, reports, favorites, moderation):
    app.include_router(module.router, prefix=settings.api_prefix)

app.mount("/media", StaticFiles(directory=settings.upload_dir), name="media")


@app.get("/health", tags=["System"], summary="Kiểm tra API và CSDL (dùng cho Docker healthcheck)")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("health_check_db_failed")
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "down"})
    return {"status": "ok", "database": "up"}
