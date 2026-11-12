"""Băm mật khẩu bằng Argon2id (argon2-cffi). Không bao giờ lưu hay log mật khẩu gốc."""
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# Hash giả để login với email không tồn tại cũng tốn thời gian như email tồn tại
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing-equalization")


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """True nếu tham số băm cũ hơn cấu hình hiện tại -> băm lại khi người dùng đăng nhập."""
    return _hasher.check_needs_rehash(hashed)


def burn_time(plain: str) -> None:
    verify_password(plain, _DUMMY_HASH)
