"""Tạo và kiểm tra JWT access token (HS256).

Payload: sub (id người dùng), iat, exp, jti, type. JWT chỉ được KÝ, không được MÃ HÓA
-> không đưa thông tin nhạy cảm vào payload. Vai trò KHÔNG nằm trong token: mỗi request
đọc lại role từ CSDL nên đổi quyền/khóa tài khoản có hiệu lực ngay."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings
from app.core.exceptions import UnauthorizedError


def create_access_token(user_id: int) -> tuple[str, int]:
    """Trả về (token, số giây hiệu lực)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_in = settings.access_token_expire_minutes * 60
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],  # cố định thuật toán, chống tấn công alg=none
            options={"require": ["exp", "iat", "sub"]},
            leeway=10,  # chịu lệch đồng hồ tối đa 10 giây
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại", code="token_expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Token không hợp lệ", code="token_invalid")
    if payload.get("type") != "access":
        raise UnauthorizedError("Token không hợp lệ", code="token_invalid")
    return payload
