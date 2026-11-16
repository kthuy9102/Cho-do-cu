import logging
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import get_settings
from app.models import User

API = "/api/v1"


def register(client, **overrides):
    body = {"email": "new@example.com", "password": "Abc12345", "full_name": "Nguyen Van New"}
    body.update(overrides)
    return client.post(f"{API}/auth/register", json=body)


def make_token(user_id, **claims):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": "access", "iat": now, "exp": now + timedelta(hours=1)}
    payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- đăng ký ----------

def test_register_success(client, db):
    response = register(client, email="New@Example.com")
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"  # chuẩn hóa về chữ thường
    assert data["role"] == "student"
    assert "password" not in data and "hashed_password" not in data
    stored = db.query(User).filter_by(email="new@example.com").one()
    assert stored.hashed_password.startswith("$argon2")  # không lưu mật khẩu gốc


def test_register_duplicate_email_is_case_insensitive(client):
    assert register(client, email="dup@example.com").status_code == 201
    response = register(client, email="DUP@example.com")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


@pytest.mark.parametrize("password", ["abcdefgh", "12345678", "abc1"])
def test_register_rejects_weak_password(client, password):
    response = register(client, password=password)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert any(item["field"] == "password" for item in error["details"])


def test_register_rejects_invalid_email(client):
    assert register(client, email="khong-phai-email").status_code == 422


def test_register_cannot_choose_role(client):
    response = register(client, role="admin")  # chống tự nâng quyền
    assert response.status_code == 422
    assert any(item["field"] == "role" for item in response.json()["error"]["details"])


# ---------- đăng nhập ----------

def test_login_success(client, alice):
    response = client.post(f"{API}/auth/login", data={"username": alice.email, "password": "Student123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == get_settings().access_token_expire_minutes * 60
    assert body["user"]["email"] == alice.email
    assert "hashed_password" not in body["user"]


def test_login_email_is_case_insensitive(client, alice):
    response = client.post(f"{API}/auth/login", data={"username": "ALICE@Example.com", "password": "Student123"})
    assert response.status_code == 200


def test_login_wrong_password_and_unknown_email_give_same_answer(client, alice):
    wrong_password = client.post(f"{API}/auth/login", data={"username": alice.email, "password": "Sai123456"})
    unknown_email = client.post(f"{API}/auth/login", data={"username": "ghost@example.com", "password": "Sai123456"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["error"]["code"] == "invalid_credentials"
    # không cho kẻ tấn công biết email nào có tồn tại
    assert wrong_password.json()["error"]["message"] == unknown_email.json()["error"]["message"]


def test_login_inactive_account_is_blocked(client, make_user):
    user = make_user("locked@example.com", is_active=False)
    response = client.post(f"{API}/auth/login", data={"username": user.email, "password": "Student123"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "account_disabled"


def test_login_is_throttled_after_repeated_failures(client, alice):
    for _ in range(5):
        wrong = client.post(f"{API}/auth/login", data={"username": alice.email, "password": "Sai123456"})
        assert wrong.status_code == 401
    blocked = client.post(f"{API}/auth/login", data={"username": alice.email, "password": "Student123"})
    assert blocked.status_code == 429  # kể cả khi lần này nhập đúng
    assert blocked.json()["error"]["code"] == "too_many_attempts"
    assert int(blocked.headers["Retry-After"]) > 0


# ---------- token ----------

def test_protected_endpoint_without_token_returns_401(client):
    response = client.get(f"{API}/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
    assert response.headers["www-authenticate"] == "Bearer"


def test_garbage_token_is_rejected(client):
    response = client.get(f"{API}/users/me", headers=bearer("khong-phai-jwt"))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_invalid"


def test_expired_token_is_reported_as_expired(client, alice):
    now = datetime.now(timezone.utc)
    token = make_token(alice.id, iat=now - timedelta(hours=2), exp=now - timedelta(hours=1))
    response = client.get(f"{API}/users/me", headers=bearer(token))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_expired"


def test_token_signed_with_other_key_is_rejected(client, alice):
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {"sub": str(alice.id), "type": "access", "iat": now, "exp": now + timedelta(hours=1)},
        "mot-khoa-bi-mat-khac-hoan-toan-0123456789",
        algorithm="HS256",
    )
    response = client.get(f"{API}/users/me", headers=bearer(forged))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_invalid"


def test_unsigned_token_alg_none_is_rejected(client, alice):
    now = datetime.now(timezone.utc)
    unsigned = jwt.encode(
        {"sub": str(alice.id), "type": "access", "iat": now, "exp": now + timedelta(hours=1)}, None, algorithm="none"
    )
    response = client.get(f"{API}/users/me", headers=bearer(unsigned))
    assert response.status_code == 401


def test_token_of_wrong_type_is_rejected(client, alice):
    response = client.get(f"{API}/users/me", headers=bearer(make_token(alice.id, type="refresh")))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_invalid"


def test_token_of_nonexistent_user_is_rejected(client):
    response = client.get(f"{API}/users/me", headers=bearer(make_token(999999)))
    assert response.status_code == 401


def test_me_returns_current_user(client, alice, login):
    response = client.get(f"{API}/users/me", headers=login(alice.email))
    assert response.status_code == 200
    assert response.json()["email"] == alice.email


# ---------- đổi mật khẩu ----------

def test_change_password_flow(client, alice, login):
    headers = login(alice.email)
    url = f"{API}/auth/change-password"

    wrong = client.post(url, json={"current_password": "Sai123456", "new_password": "NewPass123"}, headers=headers)
    assert wrong.status_code == 400 and wrong.json()["error"]["code"] == "wrong_current_password"

    same = client.post(url, json={"current_password": "Student123", "new_password": "Student123"}, headers=headers)
    assert same.status_code == 400 and same.json()["error"]["code"] == "password_unchanged"

    weak = client.post(url, json={"current_password": "Student123", "new_password": "chuaso"}, headers=headers)
    assert weak.status_code == 422

    ok = client.post(url, json={"current_password": "Student123", "new_password": "NewPass123"}, headers=headers)
    assert ok.status_code == 200

    old_login = client.post(f"{API}/auth/login", data={"username": alice.email, "password": "Student123"})
    assert old_login.status_code == 401
    new_login = client.post(f"{API}/auth/login", data={"username": alice.email, "password": "NewPass123"})
    assert new_login.status_code == 200


# ---------- logging bảo mật ----------

def test_failed_login_is_logged_without_leaking_password(client, alice, caplog):
    with caplog.at_level(logging.INFO):
        client.post(f"{API}/auth/login", data={"username": alice.email, "password": "TopSecret999"})
    failed = [r for r in caplog.records if r.getMessage() == "login_failed"]
    assert failed and failed[0].email == alice.email
    assert not any("TopSecret999" in str(record.__dict__) for record in caplog.records)
