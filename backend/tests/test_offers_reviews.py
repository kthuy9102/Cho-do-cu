import pytest

from app.models import Listing, ListingStatus

API = "/api/v1"


def make_offer(client, listing_id, headers, amount=40000):
    return client.post(f"{API}/listings/{listing_id}/offers", json={"amount": amount, "message": "Bán cho mình nhé"}, headers=headers)


def complete_deal(client, listing_id, seller_headers, buyer_headers, amount=40000):
    created = make_offer(client, listing_id, buyer_headers, amount)
    assert created.status_code == 201, created.text
    offer_id = created.json()["id"]
    accepted = client.post(f"{API}/offers/{offer_id}/accept", headers=seller_headers)
    assert accepted.status_code == 200, accepted.text
    return offer_id


@pytest.fixture()
def listing(alice, category, make_listing):
    return make_listing(alice, category)


# ---------- tạo đề nghị ----------

def test_buyer_creates_offer(client, alice, bob, listing, login):
    response = make_offer(client, listing.id, login(bob.email))
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending" and data["amount"] == 40000
    assert data["buyer"]["id"] == bob.id and data["listing"]["id"] == listing.id


def test_guest_cannot_make_offer(client, listing):
    assert client.post(f"{API}/listings/{listing.id}/offers", json={"amount": 1000}).status_code == 401


def test_cannot_offer_on_own_listing(client, alice, listing, login):
    response = make_offer(client, listing.id, login(alice.email))
    assert response.status_code == 403 and response.json()["error"]["code"] == "own_listing"


def test_cannot_offer_on_unapproved_or_missing_listing(client, alice, bob, category, make_listing, login):
    pending = make_listing(alice, category, status=ListingStatus.pending)
    assert make_offer(client, pending.id, login(bob.email)).status_code == 404
    assert make_offer(client, 99999, login(bob.email)).status_code == 404


def test_cannot_offer_on_sold_listing(client, alice, bob, category, make_listing, login):
    sold = make_listing(alice, category, status=ListingStatus.sold)
    response = make_offer(client, sold.id, login(bob.email))
    assert response.status_code == 409 and response.json()["error"]["code"] == "listing_not_available"


@pytest.mark.parametrize("payload", [{"amount": 0}, {"amount": -5}, {}, {"amount": "nhiều"}, {"amount": 100, "status": "accepted"}])
def test_offer_validation(client, bob, listing, login, payload):
    response = client.post(f"{API}/listings/{listing.id}/offers", json=payload, headers=login(bob.email))
    assert response.status_code == 422


def test_duplicate_pending_offer_is_rejected_until_cancelled(client, bob, listing, login):
    headers = login(bob.email)
    first = make_offer(client, listing.id, headers)
    second = make_offer(client, listing.id, headers)
    assert second.status_code == 409 and second.json()["error"]["code"] == "duplicate_offer"

    assert client.post(f"{API}/offers/{first.json()['id']}/cancel", headers=headers).status_code == 200
    assert make_offer(client, listing.id, headers).status_code == 201


# ---------- chấp nhận / từ chối / hủy ----------

def test_accept_sells_listing_and_rejects_other_pending_offers(client, db, alice, bob, carol, listing, login):
    bob_headers, carol_headers, alice_headers = login(bob.email), login(carol.email), login(alice.email)
    bob_offer = make_offer(client, listing.id, bob_headers, 40000).json()["id"]
    carol_offer = make_offer(client, listing.id, carol_headers, 45000).json()["id"]

    accepted = client.post(f"{API}/offers/{bob_offer}/accept", headers=alice_headers)
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert accepted.json()["listing"]["status"] == "sold"

    db.expire_all()
    assert db.get(Listing, listing.id).status == ListingStatus.sold
    carol_view = client.get(f"{API}/offers/{carol_offer}", headers=carol_headers).json()
    assert carol_view["status"] == "rejected"
    assert client.get(f"{API}/listings").json()["total"] == 0


def test_accept_twice_and_accept_losing_offer_conflict(client, alice, bob, carol, listing, login):
    alice_headers = login(alice.email)
    bob_offer = make_offer(client, listing.id, login(bob.email)).json()["id"]
    carol_offer = make_offer(client, listing.id, login(carol.email)).json()["id"]
    assert client.post(f"{API}/offers/{bob_offer}/accept", headers=alice_headers).status_code == 200

    again = client.post(f"{API}/offers/{bob_offer}/accept", headers=alice_headers)
    assert again.status_code == 409 and again.json()["error"]["code"] == "offer_not_pending"
    late = client.post(f"{API}/offers/{carol_offer}/accept", headers=alice_headers)
    assert late.status_code == 409


def test_only_the_seller_can_accept_or_reject(client, alice, bob, carol, listing, login):
    offer_id = make_offer(client, listing.id, login(bob.email)).json()["id"]
    for who in (bob, carol):  # người mua và người lạ đều nhận 404, không biết đề nghị có tồn tại
        assert client.post(f"{API}/offers/{offer_id}/accept", headers=login(who.email)).status_code == 404
        assert client.post(f"{API}/offers/{offer_id}/reject", headers=login(who.email)).status_code == 404
    assert client.post(f"{API}/offers/99999/accept", headers=login(alice.email)).status_code == 404


def test_seller_rejects_offer(client, alice, bob, listing, login):
    offer_id = make_offer(client, listing.id, login(bob.email)).json()["id"]
    headers = login(alice.email)
    rejected = client.post(f"{API}/offers/{offer_id}/reject", headers=headers)
    assert rejected.status_code == 200 and rejected.json()["status"] == "rejected"
    assert client.post(f"{API}/offers/{offer_id}/reject", headers=headers).status_code == 409


def test_cancel_rules(client, alice, bob, carol, listing, login):
    offer_id = make_offer(client, listing.id, login(bob.email)).json()["id"]
    assert client.post(f"{API}/offers/{offer_id}/cancel", headers=login(carol.email)).status_code == 404
    assert client.post(f"{API}/offers/{offer_id}/cancel", headers=login(alice.email)).status_code == 404

    assert client.post(f"{API}/offers/{offer_id}/accept", headers=login(alice.email)).status_code == 200
    late = client.post(f"{API}/offers/{offer_id}/cancel", headers=login(bob.email))
    assert late.status_code == 409 and late.json()["error"]["code"] == "offer_not_pending"


def test_offer_lists_and_visibility(client, alice, bob, carol, listing, login):
    bob_offer = make_offer(client, listing.id, login(bob.email)).json()["id"]

    sent = client.get(f"{API}/offers/sent", headers=login(bob.email)).json()
    assert sent["total"] == 1 and sent["items"][0]["id"] == bob_offer
    assert client.get(f"{API}/offers/sent", params={"status": "accepted"}, headers=login(bob.email)).json()["total"] == 0

    received = client.get(f"{API}/offers/received", headers=login(alice.email)).json()
    assert received["total"] == 1
    by_listing = client.get(f"{API}/offers/received", params={"listing_id": 99999}, headers=login(alice.email)).json()
    assert by_listing["total"] == 0
    assert client.get(f"{API}/offers/received", headers=login(bob.email)).json()["total"] == 0

    for who, expected in ((alice, 200), (bob, 200), (carol, 404)):
        assert client.get(f"{API}/offers/{bob_offer}", headers=login(who.email)).status_code == expected


# ---------- đánh giá và điểm uy tín ----------

def test_review_flow_and_rules(client, alice, bob, carol, listing, login):
    bob_headers, alice_headers = login(bob.email), login(alice.email)
    offer_id = make_offer(client, listing.id, bob_headers).json()["id"]
    url = f"{API}/offers/{offer_id}/review"

    early = client.post(url, json={"rating": 5}, headers=bob_headers)
    assert early.status_code == 409 and early.json()["error"]["code"] == "offer_not_accepted"

    client.post(f"{API}/offers/{offer_id}/accept", headers=alice_headers)

    assert client.post(url, json={"rating": 6}, headers=bob_headers).status_code == 422
    assert client.post(url, json={"rating": 0}, headers=bob_headers).status_code == 422
    assert client.post(url, json={"rating": 5}, headers=login(carol.email)).status_code == 404
    assert client.post(url, json={"rating": 5}, headers=alice_headers).status_code == 404  # người bán không tự đánh giá

    created = client.post(url, json={"rating": 5, "comment": "Giao dịch nhanh gọn"}, headers=bob_headers)
    assert created.status_code == 201
    assert created.json()["reviewer"]["id"] == bob.id and created.json()["seller_id"] == alice.id

    again = client.post(url, json={"rating": 1}, headers=bob_headers)
    assert again.status_code == 409 and again.json()["error"]["code"] == "already_reviewed"


def test_seller_reputation_is_average_of_ratings(client, alice, bob, category, make_listing, login):
    alice_headers, bob_headers = login(alice.email), login(bob.email)
    first = make_listing(alice, category, title="Món đồ thứ nhất")
    second = make_listing(alice, category, title="Món đồ thứ hai")
    for listing_item, rating in ((first, 5), (second, 3)):
        offer_id = complete_deal(client, listing_item.id, alice_headers, bob_headers)
        assert client.post(f"{API}/offers/{offer_id}/review", json={"rating": rating}, headers=bob_headers).status_code == 201

    profile = client.get(f"{API}/users/{alice.id}").json()
    assert profile["rating_avg"] == 4.0 and profile["review_count"] == 2
    reviews = client.get(f"{API}/users/{alice.id}/reviews").json()
    assert reviews["total"] == 2
    assert client.get(f"{API}/users/99999/reviews").status_code == 404


# ---------- báo cáo vi phạm ----------

def report(client, listing_id, headers, reason="spam"):
    return client.post(f"{API}/listings/{listing_id}/reports", json={"reason_code": reason, "detail": "Tin lặp lại nhiều lần"}, headers=headers)


def test_report_rules(client, alice, bob, category, make_listing, listing, login):
    created = report(client, listing.id, login(bob.email))
    assert created.status_code == 201 and created.json()["status"] == "open"

    duplicate = report(client, listing.id, login(bob.email))
    assert duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "already_reported"
    assert report(client, listing.id, login(alice.email)).status_code == 403
    assert report(client, listing.id, login(bob.email), reason="khong-co").status_code == 422
    pending = make_listing(alice, category, status=ListingStatus.pending)
    assert report(client, pending.id, login(bob.email)).status_code == 404


def test_only_staff_can_read_reports(client, alice, bob, mod, listing, login):
    report(client, listing.id, login(bob.email))
    assert client.get(f"{API}/moderation/reports", headers=login(alice.email)).status_code == 403
    queue = client.get(f"{API}/moderation/reports", headers=login(mod.email)).json()
    assert queue["total"] == 1 and queue["items"][0]["reporter"]["id"] == bob.id


def test_resolving_report_by_hiding_listing(client, db, alice, bob, carol, mod, listing, login):
    offer_id = make_offer(client, listing.id, login(carol.email)).json()["id"]
    report_id = report(client, listing.id, login(bob.email)).json()["id"]
    url = f"{API}/moderation/reports/{report_id}"

    resolved = client.patch(url, json={"action": "hide_listing", "note": "Spam"}, headers=login(mod.email))
    assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"

    db.expire_all()
    assert db.get(Listing, listing.id).status == ListingStatus.hidden
    assert client.get(f"{API}/offers/{offer_id}", headers=login(carol.email)).json()["status"] == "rejected"
    assert client.get(f"{API}/listings").json()["total"] == 0

    again = client.patch(url, json={"action": "dismiss"}, headers=login(mod.email))
    assert again.status_code == 409 and again.json()["error"]["code"] == "report_already_resolved"


def test_dismissing_report_keeps_listing(client, bob, mod, listing, login):
    report_id = report(client, listing.id, login(bob.email)).json()["id"]
    resolved = client.patch(f"{API}/moderation/reports/{report_id}", json={"action": "dismiss"}, headers=login(mod.email))
    assert resolved.status_code == 200 and resolved.json()["status"] == "dismissed"
    assert client.get(f"{API}/listings").json()["total"] == 1


def test_cannot_hide_sold_listing_and_invalid_action(client, alice, bob, mod, category, make_listing, login):
    sold = make_listing(alice, category, status=ListingStatus.sold)
    report_id = report(client, sold.id, login(bob.email)).json()["id"]
    url = f"{API}/moderation/reports/{report_id}"
    assert client.patch(url, json={"action": "xoa-het"}, headers=login(mod.email)).status_code == 422
    blocked = client.patch(url, json={"action": "hide_listing"}, headers=login(mod.email))
    assert blocked.status_code == 409 and blocked.json()["error"]["code"] == "listing_sold"
    assert client.patch(f"{API}/moderation/reports/99999", json={"action": "dismiss"}, headers=login(mod.email)).status_code == 404


# ---------- yêu thích ----------

def test_favorites_flow_is_idempotent(client, bob, listing, login):
    headers = login(bob.email)
    url = f"{API}/listings/{listing.id}/favorite"
    assert client.put(url, headers=headers).status_code == 204
    assert client.put(url, headers=headers).status_code == 204
    favorites = client.get(f"{API}/favorites", headers=headers).json()
    assert favorites["total"] == 1 and favorites["items"][0]["id"] == listing.id
    assert client.delete(url, headers=headers).status_code == 204
    assert client.delete(url, headers=headers).status_code == 204
    assert client.get(f"{API}/favorites", headers=headers).json()["total"] == 0


def test_cannot_favorite_unapproved_listing(client, alice, bob, category, make_listing, login):
    pending = make_listing(alice, category, status=ListingStatus.pending)
    assert client.put(f"{API}/listings/{pending.id}/favorite", headers=login(bob.email)).status_code == 404
