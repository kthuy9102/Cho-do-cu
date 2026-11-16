from pathlib import Path

import pytest
from sqlalchemy import event

from app.config import get_settings
from app.models import ItemCondition, ListingStatus

API = "/api/v1"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def body(category_id, **overrides):
    data = {
        "title": "Giáo trình Giải tích 1",
        "description": "Sách còn mới, ít ghi chú bên trong",
        "price": 45000,
        "condition": "good",
        "category_id": category_id,
    }
    data.update(overrides)
    return data


def upload(client, listing_id, headers, files):
    return client.post(
        f"{API}/listings/{listing_id}/images",
        files=[("files", (name, content, ctype)) for name, content, ctype in files],
        headers=headers,
    )


# ---------- đăng tin và kiểm duyệt ----------

def test_create_listing_starts_pending(client, alice, category, login):
    response = client.post(f"{API}/listings", json=body(category.id), headers=login(alice.email))
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["seller"]["id"] == alice.id
    assert data["images"] == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"price": -1},
        {"title": "abc"},
        {"description": "ngắn"},
        {"condition": "xin-xo"},
        {"status": "approved"},  # client không được tự chọn trạng thái
        {"seller_id": 1},
    ],
)
def test_create_listing_validation(client, alice, category, login, overrides):
    response = client.post(f"{API}/listings", json=body(category.id, **overrides), headers=login(alice.email))
    assert response.status_code == 422


def test_create_listing_with_unknown_category(client, alice, login):
    response = client.post(f"{API}/listings", json=body(9999), headers=login(alice.email))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_category"


def test_pending_listing_is_visible_only_to_owner_and_staff(client, alice, bob, mod, category, login):
    created = client.post(f"{API}/listings", json=body(category.id), headers=login(alice.email)).json()
    url = f"{API}/listings/{created['id']}"

    assert client.get(f"{API}/listings").json()["total"] == 0
    assert client.get(url).status_code == 404  # khách
    assert client.get(url, headers=login(bob.email)).status_code == 404  # người khác
    assert client.get(url, headers=login(alice.email)).status_code == 200  # chủ tin
    assert client.get(url, headers=login(mod.email)).status_code == 200  # kiểm duyệt viên
    assert client.get(f"{API}/listings/mine", headers=login(alice.email)).json()["total"] == 1


def test_moderator_approves_and_listing_becomes_public(client, alice, mod, category, make_listing, login):
    listing = make_listing(alice, category, status=ListingStatus.pending)
    headers = login(mod.email)

    approved = client.post(f"{API}/moderation/listings/{listing.id}/approve", headers=headers)
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert client.get(f"{API}/listings").json()["total"] == 1

    again = client.post(f"{API}/moderation/listings/{listing.id}/approve", headers=headers)
    assert again.status_code == 409 and again.json()["error"]["code"] == "listing_not_pending"


def test_reject_needs_reason_and_owner_can_see_it(client, alice, mod, category, make_listing, login):
    listing = make_listing(alice, category, status=ListingStatus.pending)
    headers = login(mod.email)
    url = f"{API}/moderation/listings/{listing.id}/reject"

    assert client.post(url, json={"reason": "x"}, headers=headers).status_code == 422
    rejected = client.post(url, json={"reason": "Ảnh không đúng sản phẩm"}, headers=headers)
    assert rejected.status_code == 200 and rejected.json()["status"] == "rejected"

    mine = client.get(f"{API}/listings/mine", params={"status": "rejected"}, headers=login(alice.email)).json()
    assert mine["items"][0]["reject_reason"] == "Ảnh không đúng sản phẩm"
    assert client.get(f"{API}/listings").json()["total"] == 0


def test_moderator_cannot_approve_own_listing(client, mod, category, make_listing, login):
    listing = make_listing(mod, category, status=ListingStatus.pending)
    response = client.post(f"{API}/moderation/listings/{listing.id}/approve", headers=login(mod.email))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "self_moderation"


def test_moderation_queue_lists_pending_oldest_first(client, alice, mod, category, make_listing, login):
    first = make_listing(alice, category, status=ListingStatus.pending, title="Tin đăng đầu tiên")
    make_listing(alice, category, status=ListingStatus.pending, title="Tin đăng thứ hai")
    make_listing(alice, category, status=ListingStatus.approved, title="Tin đã duyệt rồi")
    queue = client.get(f"{API}/moderation/listings", headers=login(mod.email)).json()
    assert queue["total"] == 2
    assert queue["items"][0]["id"] == first.id


# ---------- sửa / xóa ----------

def test_editing_approved_listing_sends_it_back_to_moderation(client, alice, category, make_listing, login):
    listing = make_listing(alice, category)
    response = client.patch(f"{API}/listings/{listing.id}", json={"price": 99000}, headers=login(alice.email))
    assert response.status_code == 200
    assert response.json()["price"] == 99000
    assert response.json()["status"] == "pending"
    assert client.get(f"{API}/listings").json()["total"] == 0


def test_only_owner_can_edit(client, alice, bob, category, make_listing, login):
    approved = make_listing(alice, category)
    pending = make_listing(alice, category, status=ListingStatus.pending)
    headers = login(bob.email)
    forbidden = client.patch(f"{API}/listings/{approved.id}", json={"price": 1}, headers=headers)
    assert forbidden.status_code == 403 and forbidden.json()["error"]["code"] == "not_owner"
    assert client.patch(f"{API}/listings/{pending.id}", json={"price": 1}, headers=headers).status_code == 404


def test_cannot_edit_sold_listing(client, alice, category, make_listing, login):
    sold = make_listing(alice, category, status=ListingStatus.sold)
    response = client.patch(f"{API}/listings/{sold.id}", json={"price": 1}, headers=login(alice.email))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "listing_not_editable"


@pytest.mark.parametrize("payload", [{}, {"title": None}, {"price": -5}, {"category_id": 0}])
def test_patch_validation(client, alice, category, make_listing, login, payload):
    listing = make_listing(alice, category)
    assert client.patch(f"{API}/listings/{listing.id}", json=payload, headers=login(alice.email)).status_code == 422


def test_patch_with_unknown_category(client, alice, category, make_listing, login):
    listing = make_listing(alice, category)
    response = client.patch(f"{API}/listings/{listing.id}", json={"category_id": 9999}, headers=login(alice.email))
    assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_category"


def test_delete_rules(client, alice, bob, mod, category, make_listing, login):
    mine = make_listing(alice, category)
    other = make_listing(alice, category, title="Tin khác của Alice")
    sold = make_listing(alice, category, status=ListingStatus.sold, title="Tin đã bán rồi")

    assert client.delete(f"{API}/listings/{mine.id}", headers=login(bob.email)).status_code == 403
    assert client.delete(f"{API}/listings/{mine.id}", headers=login(alice.email)).status_code == 204
    assert client.get(f"{API}/listings/{mine.id}").status_code == 404
    assert client.delete(f"{API}/listings/{other.id}", headers=login(mod.email)).status_code == 204
    blocked = client.delete(f"{API}/listings/{sold.id}", headers=login(alice.email))
    assert blocked.status_code == 409 and blocked.json()["error"]["code"] == "listing_sold"


def test_daily_listing_limit(client, alice, category, login):
    headers = login(alice.email)
    for index in range(5):
        response = client.post(f"{API}/listings", json=body(category.id, title=f"Tin số {index} của Alice"), headers=headers)
        assert response.status_code == 201
    sixth = client.post(f"{API}/listings", json=body(category.id, title="Tin thứ sáu bị chặn"), headers=headers)
    assert sixth.status_code == 429
    assert sixth.json()["error"]["code"] == "daily_listing_limit"


# ---------- tìm kiếm, lọc, sắp xếp, phân trang ----------

@pytest.fixture()
def three_listings(alice, category, make_listing):
    make_listing(alice, category, title="Giáo trình Giải tích 1", price=30000)
    make_listing(alice, category, title="Máy tính Casio fx-580", price=250000, description="Máy tính cầm tay còn bảo hành")
    make_listing(alice, category, title="Giáo trình Đại số", price=20000, condition=ItemCondition.fair)


def titles(response):
    return [item["title"] for item in response.json()["items"]]


def test_public_list_shows_only_approved(client, alice, category, make_listing):
    make_listing(alice, category, title="Tin đang bán")
    for status in (ListingStatus.pending, ListingStatus.rejected, ListingStatus.sold, ListingStatus.hidden):
        make_listing(alice, category, status=status, title=f"Tin trạng thái {status.value}")
    assert titles(client.get(f"{API}/listings")) == ["Tin đang bán"]


def test_search_by_keyword_in_title_and_description(client, three_listings):
    assert client.get(f"{API}/listings", params={"q": "giáo trình"}).json()["total"] == 2
    assert titles(client.get(f"{API}/listings", params={"q": "bảo hành"})) == ["Máy tính Casio fx-580"]


def test_search_wildcards_are_escaped(client, three_listings):
    assert client.get(f"{API}/listings", params={"q": "%"}).json()["total"] == 0
    assert client.get(f"{API}/listings", params={"q": "_"}).json()["total"] == 0


def test_filter_by_price_range_category_and_condition(client, alice, three_listings, make_category, make_listing):
    ranged = client.get(f"{API}/listings", params={"min_price": 25000, "max_price": 100000})
    assert titles(ranged) == ["Giáo trình Giải tích 1"]

    other = make_category("Đồ điện tử")
    make_listing(alice, other, title="Tai nghe Bluetooth", price=150000)
    assert titles(client.get(f"{API}/listings", params={"category_id": other.id})) == ["Tai nghe Bluetooth"]

    assert titles(client.get(f"{API}/listings", params={"condition": "fair"})) == ["Giáo trình Đại số"]


def test_sorting(client, three_listings):
    assert titles(client.get(f"{API}/listings")) == ["Giáo trình Đại số", "Máy tính Casio fx-580", "Giáo trình Giải tích 1"]
    asc = [item["price"] for item in client.get(f"{API}/listings", params={"sort": "price_asc"}).json()["items"]]
    desc = [item["price"] for item in client.get(f"{API}/listings", params={"sort": "price_desc"}).json()["items"]]
    assert asc == [20000, 30000, 250000]
    assert desc == [250000, 30000, 20000]


def test_pagination_has_no_overlap(client, three_listings):
    first = client.get(f"{API}/listings", params={"page": 1, "page_size": 2}).json()
    second = client.get(f"{API}/listings", params={"page": 2, "page_size": 2}).json()
    assert first["total"] == 3 and first["pages"] == 2
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    ids = [item["id"] for item in first["items"] + second["items"]]
    assert len(set(ids)) == 3


@pytest.mark.parametrize(
    "params",
    [
        {"min_price": 500, "max_price": 100},
        {"page": 0},
        {"page_size": 101},
        {"sort": "ngau-nhien"},
        {"min_price": -1},
        {"category_id": 0},
    ],
)
def test_search_rejects_invalid_params(client, params):
    assert client.get(f"{API}/listings", params=params).status_code == 422


def test_list_does_not_run_one_query_per_listing(client, alice, category, make_listing, session_factory):
    """Chống lỗi N+1: số câu SQL không được tăng theo số tin."""
    for index in range(20):
        make_listing(alice, category, title=f"Tin đăng số {index:02d}")
    statements = []
    engine = session_factory.kw["bind"]

    def count(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        response = client.get(f"{API}/listings", params={"page_size": 20})
    finally:
        event.remove(engine, "before_cursor_execute", count)
    assert response.status_code == 200 and len(response.json()["items"]) == 20
    assert len(statements) <= 5, f"{len(statements)} câu SQL cho 20 tin"


# ---------- ảnh ----------

def test_upload_serve_and_delete_image(client, alice, category, make_listing, login):
    listing = make_listing(alice, category, status=ListingStatus.pending)
    headers = login(alice.email)

    response = upload(client, listing.id, headers, [("a.png", PNG, "image/png")])
    assert response.status_code == 201
    image = response.json()[0]
    assert image["url"].startswith(f"/media/listings/{listing.id}/") and image["url"].endswith(".png")

    served = client.get(image["url"])
    assert served.status_code == 200 and served.content == PNG
    on_disk = Path(get_settings().upload_dir) / image["url"].removeprefix("/media/")
    assert on_disk.is_file()

    assert client.delete(f"{API}/listings/{listing.id}/images/{image['id']}", headers=headers).status_code == 204
    assert not on_disk.exists()
    assert client.delete(f"{API}/listings/{listing.id}/images/{image['id']}", headers=headers).status_code == 404


def test_upload_rejects_fake_image_and_wrong_type(client, alice, category, make_listing, login):
    listing = make_listing(alice, category)
    headers = login(alice.email)
    fake = upload(client, listing.id, headers, [("a.png", b"day khong phai anh that", "image/png")])
    assert fake.status_code == 415 and fake.json()["error"]["code"] == "invalid_image_content"
    wrong = upload(client, listing.id, headers, [("a.txt", b"hello", "text/plain")])
    assert wrong.status_code == 415 and wrong.json()["error"]["code"] == "invalid_image_type"


def test_upload_rejects_oversized_image(client, alice, category, make_listing, login, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_size_mb", 0)
    listing = make_listing(alice, category)
    response = upload(client, listing.id, login(alice.email), [("a.png", PNG, "image/png")])
    assert response.status_code == 413 and response.json()["error"]["code"] == "image_too_large"


def test_upload_limit_per_listing(client, alice, category, make_listing, login):
    listing = make_listing(alice, category)
    headers = login(alice.email)
    five = [(f"{i}.png", PNG, "image/png") for i in range(5)]
    assert upload(client, listing.id, headers, five).status_code == 201
    extra = upload(client, listing.id, headers, [("6.png", PNG, "image/png")])
    assert extra.status_code == 409 and extra.json()["error"]["code"] == "image_limit_reached"


def test_upload_only_by_owner_and_requires_moderation_again(client, alice, bob, category, make_listing, login):
    listing = make_listing(alice, category)
    assert upload(client, listing.id, login(bob.email), [("a.png", PNG, "image/png")]).status_code == 403
    assert upload(client, listing.id, login(alice.email), [("a.png", PNG, "image/png")]).status_code == 201
    detail = client.get(f"{API}/listings/{listing.id}", headers=login(alice.email)).json()
    assert detail["status"] == "pending"
    assert detail["thumbnail_url"] == detail["images"][0]["url"]


def test_deleting_listing_removes_its_image_files(client, alice, category, make_listing, login):
    listing = make_listing(alice, category, status=ListingStatus.pending)
    headers = login(alice.email)
    image = upload(client, listing.id, headers, [("a.png", PNG, "image/png")]).json()[0]
    on_disk = Path(get_settings().upload_dir) / image["url"].removeprefix("/media/")
    assert on_disk.is_file()
    assert client.delete(f"{API}/listings/{listing.id}", headers=headers).status_code == 204
    assert not on_disk.exists()
