import logging

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.database import get_db
from app.models import Role, User
from app.schemas.auth import PasswordChange, RegisterRequest, TokenResponse
from app.schemas.common import Message, error_responses
from app.schemas.user import UserRead
from app.security.dependencies import get_current_user
from app.security.passwords import burn_time, hash_password, needs_rehash, verify_password
from app.security.throttle import login_throttle
from app.security.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("app.security")


@router.post(
    "/register",
    response_model=UserRead,
    status_code=201,
    summary="Đăng ký tài khoản sinh viên",
    responses=error_responses(409, 422),
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == payload.email)):
        raise ConflictError("Email đã được sử dụng", code="email_taken")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        student_id=payload.student_id,
        role=Role.student,  # luôn là student; moderator/admin chỉ do admin cấp hoặc seed
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # hai request đăng ký cùng email chạy song song
        db.rollback()
        raise ConflictError("Email đã được sử dụng", code="email_taken")
    db.refresh(user)  # nạp created_at do CSDL sinh
    logger.info("user_registered", extra={"user_id": user.id})
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập, nhận JWT",
    description="Form `application/x-www-form-urlencoded` theo chuẩn OAuth2: `username` là **email**, `password`.",
    responses=error_responses(401, 403, 422, 429),
)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form.username.strip().lower()
    ip = request.client.host if request.client else "unknown"
    key = f"{ip}:{email}"
    login_throttle.check(key)

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        burn_time(form.password)  # thời gian phản hồi không tiết lộ email có tồn tại hay không
        valid = False
    else:
        valid = verify_password(form.password, user.hashed_password)

    if not valid or user is None:
        login_throttle.record_failure(key)
        logger.warning("login_failed", extra={"email": email, "client_ip": ip})
        # Cùng một thông báo cho "sai email" và "sai mật khẩu"
        raise UnauthorizedError("Email hoặc mật khẩu không đúng", code="invalid_credentials")
    if not user.is_active:
        logger.warning("login_blocked_inactive", extra={"user_id": user.id, "client_ip": ip})
        raise ForbiddenError("Tài khoản đã bị khóa", code="account_disabled")

    login_throttle.reset(key)
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(form.password)
        db.commit()

    token, expires_in = create_access_token(user.id)
    logger.info("login_success", extra={"user_id": user.id, "client_ip": ip})
    return TokenResponse(access_token=token, expires_in=expires_in, user=UserRead.model_validate(user))


@router.post(
    "/change-password",
    response_model=Message,
    summary="Đổi mật khẩu",
    responses=error_responses(400, 401, 403, 422),
)
def change_password(
    payload: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, user.hashed_password):
        logger.warning("change_password_wrong_current", extra={"user_id": user.id})
        raise BadRequestError("Mật khẩu hiện tại không đúng", code="wrong_current_password")
    if payload.current_password == payload.new_password:
        raise BadRequestError("Mật khẩu mới phải khác mật khẩu hiện tại", code="password_unchanged")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    logger.info("password_changed", extra={"user_id": user.id})
    return Message(message="Đổi mật khẩu thành công")
