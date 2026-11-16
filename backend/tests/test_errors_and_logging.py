import json
import logging

from fastapi.testclient import TestClient

from app.core.logging_config import JsonFormatter
from app.main import app

API = "/api/v1"


def test_error_uses_common_envelope_with_request_id(client):
    response = client.get(f"{API}/listings/999999")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "listing_not_found"
    assert error["request_id"] and error["request_id"] == response.headers["X-Request-ID"]


def test_unknown_route_and_wrong_method_use_same_envelope(client):
    missing = client.get(f"{API}/khong-ton-tai")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"
    wrong_method = client.delete(f"{API}/auth/login")
    assert wrong_method.status_code == 405 and wrong_method.json()["error"]["code"] == "method_not_allowed"


def test_validation_error_lists_each_bad_field(client):
    response = client.post(f"{API}/auth/register", json={})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    fields = {item["field"] for item in error["details"]}
    assert {"email", "password", "full_name"} <= fields
    assert all(item["in"] == "body" for item in error["details"])


def test_client_supplied_request_id_is_echoed(client):
    response = client.get(f"{API}/categories", headers={"X-Request-ID": "abc-123"})
    assert response.headers["X-Request-ID"] == "abc-123"


def test_every_response_gets_a_request_id(client):
    assert client.get(f"{API}/categories").headers["X-Request-ID"]


def test_unhandled_exception_returns_generic_500(session_factory):
    def boom():
        raise RuntimeError("chi tiet noi bo khong duoc lo ra")

    app.add_api_route("/_boom", boom, methods=["GET"])
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            response = test_client.get("/_boom")
    finally:
        app.router.routes = [r for r in app.router.routes if getattr(r, "path", None) != "/_boom"]
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "chi tiet noi bo" not in response.text  # không lộ chi tiết nội bộ cho client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_each_request_is_logged_once_with_timing(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.request"):
        client.get(f"{API}/categories")
    records = [r for r in caplog.records if r.getMessage() == "request_completed"]
    assert len(records) == 1
    record = records[0]
    assert record.method == "GET" and record.path == f"{API}/categories"
    assert record.status_code == 200 and record.duration_ms >= 0


def test_permission_denied_is_logged_as_warning(client, alice, login, caplog):
    headers = login(alice.email)
    with caplog.at_level(logging.INFO):
        client.get(f"{API}/users", headers=headers)
    denied = [r for r in caplog.records if r.getMessage() == "permission_denied"]
    assert denied and denied[0].levelno == logging.WARNING
    assert denied[0].user_id == alice.id


def test_json_formatter_outputs_valid_json_with_extra_fields():
    record = logging.LogRecord("app.test", logging.INFO, __file__, 1, "su_kien_thu", (), None)
    record.user_id = 7
    record.request_id = "req-1"
    data = json.loads(JsonFormatter().format(record))
    assert data["message"] == "su_kien_thu" and data["level"] == "INFO"
    assert data["user_id"] == 7 and data["request_id"] == "req-1"
