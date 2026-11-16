"""Fixture dùng chung. Test chạy trên SQLite trong bộ nhớ nên không cần PostgreSQL/Docker.
Biến môi trường PHẢI đặt trước khi import app (cấu hình được đọc lúc import)."""
import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "unit-test-secret-key-0123456789abcdef0123456789"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="chodocu-test-")
os.environ["LOG_JSON"] = "false"
os.environ["LOG_LEVEL"] = "INFO"
# Cố định các giới hạn để test không phụ thuộc vào file .env của từng người
# (ví dụ .env đặt MAX_LISTINGS_PER_DAY=50 để chạy Postman)
os.environ["MAX_LISTINGS_PER_DAY"] = "5"
os.environ["MAX_IMAGES_PER_LISTING"] = "5"
os.environ["MAX_UPLOAD_SIZE_MB"] = "5"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.utils import slugify  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Category, ItemCondition, Listing, ListingStatus, Role, User  # noqa: E402
from app.security.passwords import hash_password  # noqa: E402
from app.security.throttle import login_throttle  # noqa: E402

PASSWORD = "Student123"
PASSWORD_HASH = hash_password(PASSWORD)  # băm một lần cho cả phiên test (Argon2 cố ý chậm)


@pytest.fixture()
def session_factory():
    """Mỗi test một CSDL SQLite mới, dùng chung một kết nối giữa các luồng của TestClient."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    login_throttle._failures.clear()  # trạng thái giới hạn đăng nhập là toàn cục, phải xóa giữa các test
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    def _make(email="user@example.com", role=Role.student, full_name="Nguyen Van A", is_active=True):
        user = User(email=email, hashed_password=PASSWORD_HASH, full_name=full_name, role=role, is_active=is_active)
        db.add(user)
        db.commit()
        return user

    return _make


@pytest.fixture()
def alice(make_user):
    return make_user("alice@example.com", full_name="Alice Nguoi Ban")


@pytest.fixture()
def bob(make_user):
    return make_user("bob@example.com", full_name="Bob Nguoi Mua")


@pytest.fixture()
def carol(make_user):
    return make_user("carol@example.com", full_name="Carol Nguoi La")


@pytest.fixture()
def mod(make_user):
    return make_user("mod@example.com", role=Role.moderator, full_name="Kiem Duyet Vien")


@pytest.fixture()
def admin(make_user):
    return make_user("admin@example.com", role=Role.admin, full_name="Quan Tri Vien")


@pytest.fixture()
def make_category(db):
    def _make(name="Giáo trình"):
        category = Category(name=name, slug=slugify(name))
        db.add(category)
        db.commit()
        return category

    return _make


@pytest.fixture()
def category(make_category):
    return make_category()


@pytest.fixture()
def make_listing(db):
    """Tạo tin trực tiếp trong CSDL (bỏ qua API và giới hạn 5 tin/ngày) để dựng dữ liệu nhanh."""

    def _make(seller, category, **overrides):
        data = {
            "title": "Giáo trình Giải tích 1",
            "description": "Sách còn mới, ít ghi chú bên trong",
            "price": 50000,
            "condition": ItemCondition.good,
            "status": ListingStatus.approved,
        }
        data.update(overrides)
        listing = Listing(seller_id=seller.id, category_id=category.id, **data)
        db.add(listing)
        db.commit()
        return listing

    return _make


@pytest.fixture()
def login(client):
    def _login(email, password=PASSWORD):
        response = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login
