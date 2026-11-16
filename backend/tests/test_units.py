import jwt
import pytest
from pydantic import ValidationError

from app.config import get_settings
from app.core.exceptions import TooManyRequestsError, UnauthorizedError
from app.core.pagination import PageParams, make_page
from app.core.utils import escape_like, slugify
from app.schemas.auth import RegisterRequest
from app.schemas.listing import ListingCreate, ListingUpdate
from app.security import throttle as throttle_module
from app.security.passwords import hash_password, needs_rehash, verify_password
from app.security.throttle import LoginThrottle
from app.security.tokens import create_access_token, decode_access_token
from app.services.uploads import _detect_extension


# ---------- mật khẩu ----------

def test_password_hash_and_verify():
    hashed = hash_password("Abc12345")
    assert hashed.startswith("$argon2id$")
    assert hashed != hash_password("Abc12345")  # mỗi lần băm có salt riêng
    assert verify_password("Abc12345", hashed)
    assert not verify_password("abc12345", hashed)
    assert not needs_rehash(hashed)


def test_verify_password_with_garbage_hash_returns_false():
    assert verify_password("Abc12345", "khong-phai-hash") is False


# ---------- JWT ----------

def test_access_token_roundtrip_has_no_role_claim():
    token, expires_in = create_access_token(42)
    payload = decode_access_token(token)
    assert payload["sub"] == "42" and payload["type"] == "access"
    assert expires_in == get_settings().access_token_expire_minutes * 60
    assert "role" not in payload and payload["jti"]


def test_tampered_token_is_rejected():
    token, _ = create_access_token(1)
    tampered = token[:-3] + ("AAA" if not token.endswith("AAA") else "BBB")
    with pytest.raises(UnauthorizedError) as info:
        decode_access_token(tampered)
    assert info.value.code == "token_invalid" and info.value.status_code == 401


def test_token_missing_required_claims_is_rejected():
    settings = get_settings()
    incomplete = jwt.encode({"sub": "1"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(UnauthorizedError):
        decode_access_token(incomplete)


# ---------- giới hạn đăng nhập ----------

def test_throttle_blocks_then_resets():
    throttle = LoginThrottle(max_failures=2, window_seconds=60)
    throttle.check("k")
    throttle.record_failure("k")
    throttle.check("k")  # mới sai 1 lần
    throttle.record_failure("k")
    with pytest.raises(TooManyRequestsError) as info:
        throttle.check("k")
    assert int(info.value.headers["Retry-After"]) > 0
    throttle.check("other-key")  # khóa khác không bị ảnh hưởng
    throttle.reset("k")
    throttle.check("k")


def test_throttle_failures_expire_after_window(monkeypatch):
    now = [1000.0]

    class FakeTime:
        @staticmethod
        def monotonic():
            return now[0]

    monkeypatch.setattr(throttle_module, "time", FakeTime)
    throttle = LoginThrottle(max_failures=2, window_seconds=10)
    throttle.record_failure("k")
    throttle.record_failure("k")
    with pytest.raises(TooManyRequestsError):
        throttle.check("k")
    now[0] += 11
    throttle.check("k")


# ---------- tiện ích ----------

def test_slugify():
    assert slugify("Đồ điện tử") == "do-dien-tu"
    assert slugify("  Sách & Vở!! ") == "sach-vo"
    assert slugify("???") == ""


def test_escape_like():
    assert escape_like("50%_a\\") == "50\\%\\_a\\\\"


def test_detect_image_type_by_signature():
    assert _detect_extension(b"\xff\xd8\xff\xe0" + b"\x00" * 8) == "jpg"
    assert _detect_extension(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4) == "png"
    assert _detect_extension(b"RIFF\x00\x00\x00\x00WEBP") == "webp"
    assert _detect_extension(b"GIF89a" + b"\x00" * 6) is None
    assert _detect_extension(b"<?php echo 1; ?>") is None


def test_make_page_computes_page_count():
    params = PageParams(page=2, page_size=10)
    assert params.offset == 10
    assert make_page([], 25, params)["pages"] == 3
    assert make_page([], 0, params)["pages"] == 0


# ---------- schema ----------

def test_register_schema_normalizes_input():
    data = RegisterRequest(email="A@Example.com", password="Abc12345", full_name="  Nguyen   Van   A ")
    assert data.email == "a@example.com" and data.full_name == "Nguyen Van A"


def test_listing_schemas_reject_unknown_and_empty_fields():
    with pytest.raises(ValidationError):
        ListingCreate(title="Tiêu đề hợp lệ", description="Mô tả đủ dài rồi", price=1, condition="good", category_id=1, status="approved")
    with pytest.raises(ValidationError):
        ListingUpdate()
    with pytest.raises(ValidationError):
        ListingUpdate(title=None)
    assert ListingUpdate(price=5).model_dump(exclude_unset=True) == {"price": 5}
