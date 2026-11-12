"""Dependency xác thực và phân quyền dùng chung cho mọi router.

Luồng: Authorization: Bearer <JWT> -> giải mã -> đọc user từ CSDL -> kiểm tra is_active -> kiểm tra role."""
import logging

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.database import get_db
from app.models import Role, User
from app.security.tokens import decode_access_token

logger = logging.getLogger("app.security")

# auto_error=False để tự trả 401 theo định dạng lỗi chung của dự án
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().api_prefix}/auth/login", auto_error=False)


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User | None:
    """Cho endpoint công khai nhưng hiển thị khác nếu đã đăng nhập. Không có token -> None."""
    if not token:
        return None
    payload = decode_access_token(token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedError("Token không hợp lệ", code="token_invalid")
    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Token không hợp lệ", code="token_invalid")
    if not user.is_active:
        raise ForbiddenError("Tài khoản đã bị khóa", code="account_disabled")
    return user


def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if user is None:
        raise UnauthorizedError("Cần đăng nhập để thực hiện thao tác này", code="not_authenticated")
    return user


def require_roles(*roles: Role):
    """Tạo dependency chỉ cho phép các vai trò được liệt kê."""
    allowed = frozenset(roles)

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            logger.warning(
                "permission_denied",
                extra={"user_id": user.id, "user_role": user.role.value, "required": sorted(r.value for r in allowed)},
            )
            raise ForbiddenError("Bạn không có quyền thực hiện thao tác này", code="forbidden")
        return user

    return checker


require_moderator = require_roles(Role.moderator, Role.admin)
require_admin = require_roles(Role.admin)
