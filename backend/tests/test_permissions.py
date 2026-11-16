import pytest

API = "/api/v1"


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/categories"),
        ("GET", "/users"),
        ("PATCH", "/users/me"),
        ("GET", "/moderation/listings"),
        ("POST", "/listings"),
        ("GET", "/listings/mine"),
        ("POST", "/listings/1/offers"),
        ("GET", "/offers/sent"),
        ("PUT", "/listings/1/favorite"),
        ("GET", "/favorites"),
        ("POST", "/offers/1/review"),
    ],
)
def test_guest_gets_401_on_protected_endpoints(client, method, path):
    response = client.request(method, f"{API}{path}")
    assert response.status_code == 401, f"{method} {path}"


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("POST", "/categories", {"name": "Sách vở"}),
        ("GET", "/users", None),
        ("PATCH", "/users/1/role", {"role": "admin"}),
        ("PATCH", "/users/1/active", {"is_active": False}),
        ("GET", "/moderation/listings", None),
        ("GET", "/moderation/reports", None),
        ("POST", "/moderation/listings/1/approve", None),
        ("PATCH", "/moderation/reports/1", {"action": "dismiss"}),
    ],
)
def test_student_gets_403_on_staff_endpoints(client, alice, login, method, path, body):
    response = client.request(method, f"{API}{path}", json=body, headers=login(alice.email))
    assert response.status_code == 403, f"{method} {path}"
    assert response.json()["error"]["code"] == "forbidden"


def test_moderator_can_moderate_but_not_administer(client, mod, login):
    headers = login(mod.email)
    assert client.get(f"{API}/moderation/listings", headers=headers).status_code == 200
    assert client.get(f"{API}/users", headers=headers).status_code == 403
    assert client.post(f"{API}/categories", json={"name": "Khác"}, headers=headers).status_code == 403


def test_admin_has_moderator_powers(client, admin, login):
    headers = login(admin.email)
    assert client.get(f"{API}/moderation/reports", headers=headers).status_code == 200
    assert client.get(f"{API}/users", headers=headers).status_code == 200


# ---------- thay đổi quyền có hiệu lực ngay ----------

def test_role_change_takes_effect_immediately(client, admin, mod, login):
    mod_headers = login(mod.email)
    assert client.get(f"{API}/moderation/listings", headers=mod_headers).status_code == 200

    demote = client.patch(f"{API}/users/{mod.id}/role", json={"role": "student"}, headers=login(admin.email))
    assert demote.status_code == 200

    # token cũ vẫn hợp lệ nhưng vai trò được đọc lại từ CSDL
    assert client.get(f"{API}/moderation/listings", headers=mod_headers).status_code == 403


def test_deactivated_user_loses_access_immediately(client, admin, alice, login):
    alice_headers = login(alice.email)
    lock = client.patch(f"{API}/users/{alice.id}/active", json={"is_active": False}, headers=login(admin.email))
    assert lock.status_code == 200

    response = client.get(f"{API}/users/me", headers=alice_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "account_disabled"
    relogin = client.post(f"{API}/auth/login", data={"username": alice.email, "password": "Student123"})
    assert relogin.status_code == 403


def test_admin_cannot_modify_own_role_or_status(client, admin, login):
    headers = login(admin.email)
    role = client.patch(f"{API}/users/{admin.id}/role", json={"role": "student"}, headers=headers)
    active = client.patch(f"{API}/users/{admin.id}/active", json={"is_active": False}, headers=headers)
    assert role.status_code == active.status_code == 403
    assert role.json()["error"]["code"] == "cannot_modify_self"


def test_admin_set_role_validates_input_and_target(client, admin, alice, login):
    headers = login(admin.email)
    assert client.patch(f"{API}/users/{alice.id}/role", json={"role": "superuser"}, headers=headers).status_code == 422
    assert client.patch(f"{API}/users/99999/role", json={"role": "moderator"}, headers=headers).status_code == 404
    ok = client.patch(f"{API}/users/{alice.id}/role", json={"role": "moderator"}, headers=headers)
    assert ok.status_code == 200 and ok.json()["role"] == "moderator"


def test_admin_user_list_supports_filter_and_paging(client, admin, alice, bob, login):
    headers = login(admin.email)
    response = client.get(f"{API}/users", params={"role": "student", "page_size": 1}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2 and body["pages"] == 2 and len(body["items"]) == 1
    found = client.get(f"{API}/users", params={"q": "alice"}, headers=headers).json()
    assert found["total"] == 1


# ---------- hồ sơ cá nhân ----------

def test_user_cannot_escalate_through_profile_update(client, alice, login):
    headers = login(alice.email)
    response = client.patch(f"{API}/users/me", json={"role": "admin"}, headers=headers)
    assert response.status_code == 422
    assert client.get(f"{API}/users/me", headers=headers).json()["role"] == "student"


def test_update_profile_normalizes_name_and_rejects_empty_body(client, alice, login):
    headers = login(alice.email)
    ok = client.patch(f"{API}/users/me", json={"full_name": "  Nguyen   Van   B "}, headers=headers)
    assert ok.status_code == 200 and ok.json()["full_name"] == "Nguyen Van B"
    assert client.patch(f"{API}/users/me", json={}, headers=headers).status_code == 422
    assert client.patch(f"{API}/users/me", json={"full_name": None}, headers=headers).status_code == 422


def test_public_profile_hides_private_fields(client, alice):
    response = client.get(f"{API}/users/{alice.id}")
    assert response.status_code == 200
    body = response.json()
    assert "email" not in body and "role" not in body
    assert body["rating_avg"] is None and body["review_count"] == 0


def test_public_profile_of_inactive_or_missing_user_is_404(client, make_user):
    locked = make_user("locked@example.com", is_active=False)
    assert client.get(f"{API}/users/{locked.id}").status_code == 404
    assert client.get(f"{API}/users/99999").status_code == 404


# ---------- danh mục (admin) ----------

def test_admin_manages_categories(client, admin, alice, make_listing, login):
    headers = login(admin.email)
    created = client.post(f"{API}/categories", json={"name": "Đồ điện tử"}, headers=headers)
    assert created.status_code == 201
    assert created.json()["slug"] == "do-dien-tu"

    duplicate = client.post(f"{API}/categories", json={"name": "Đồ điện tử"}, headers=headers)
    assert duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "category_exists"

    category_id = created.json()["id"]
    renamed = client.patch(f"{API}/categories/{category_id}", json={"name": "Điện tử"}, headers=headers)
    assert renamed.status_code == 200 and renamed.json()["slug"] == "dien-tu"

    public = client.get(f"{API}/categories")
    assert public.status_code == 200 and len(public.json()) == 1

    assert client.delete(f"{API}/categories/{category_id}", headers=headers).status_code == 204
    assert client.delete(f"{API}/categories/{category_id}", headers=headers).status_code == 404


def test_cannot_delete_category_that_has_listings(client, admin, alice, category, make_listing, login):
    make_listing(alice, category)
    response = client.delete(f"{API}/categories/{category.id}", headers=login(admin.email))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "category_in_use"
