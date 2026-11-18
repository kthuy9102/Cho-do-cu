from app.models import Listing, ListingStatus, Order, OrderStatus


API = "/api/v1"


@pytest.fixture()
def listing(alice, category, make_listing):
    return make_listing(alice, category)


def make_offer(client, listing_id, headers):
    return client.post(
        f"{API}/listings/{listing_id}/offers",
        json={"amount": 42000, "message": "Mình lấy nhé"},
        headers=headers,
    )


def test_order_lifecycle_and_notifications(client, alice, bob, carol, listing, login, db):
    seller = login(alice.email)
    buyer = login(bob.email)
    outsider = login(carol.email)

    created = make_offer(client, listing.id, buyer)
    assert created.status_code == 201, created.text
    offer_id = created.json()["id"]

    # Seller receives a persistent notification when buyer sends an offer.
    inbox = client.get(f"{API}/notifications", headers=seller).json()
    assert inbox["total"] == 1
    notification_id = inbox["items"][0]["id"]
    assert inbox["items"][0]["event_type"] == "offer_received"
    assert client.get(f"{API}/notifications", headers=buyer).json()["total"] == 0

    accepted = client.post(f"{API}/offers/{offer_id}/accept", headers=seller)
    assert accepted.status_code == 200, accepted.text

    buyer_orders = client.get(f"{API}/orders?side=buying", headers=buyer).json()
    seller_orders = client.get(f"{API}/orders?side=selling", headers=seller).json()
    assert buyer_orders["total"] == seller_orders["total"] == 1
    order = buyer_orders["items"][0]
    assert order["offer_id"] == offer_id
    assert order["status"] == "confirmed"
    assert order["buyer"]["id"] == bob.id and order["seller"]["id"] == alice.id

    order_id = order["id"]
    assert client.get(f"{API}/orders/{order_id}", headers=outsider).status_code == 404
    assert client.post(f"{API}/orders/{order_id}/ship", headers=buyer).status_code == 404
    assert client.post(f"{API}/orders/{order_id}/complete", headers=buyer).status_code == 409

    shipped = client.post(f"{API}/orders/{order_id}/ship", headers=seller)
    assert shipped.status_code == 200 and shipped.json()["status"] == "shipped"
    completed = client.post(f"{API}/orders/{order_id}/complete", headers=buyer)
    assert completed.status_code == 200 and completed.json()["status"] == "completed"

    db.expire_all()
    assert db.get(Order, order_id).status == OrderStatus.completed
    assert db.get(Listing, listing.id).status == ListingStatus.sold

    buyer_inbox = client.get(f"{API}/notifications", headers=buyer).json()
    assert {x["event_type"] for x in buyer_inbox["items"]} >= {"offer_accepted", "order_shipped"}
    count = client.get(f"{API}/notifications/unread-count", headers=buyer).json()
    assert count["unread_count"] >= 2

    read = client.patch(f"{API}/notifications/{buyer_inbox['items'][0]['id']}/read", headers=buyer)
    assert read.status_code == 200 and read.json()["read_at"] is not None
    assert client.patch(f"{API}/notifications/{notification_id}/read", headers=buyer).status_code == 404
    assert client.post(f"{API}/notifications/read-all", headers=buyer).status_code == 204
    assert client.get(f"{API}/notifications/unread-count", headers=buyer).json()["unread_count"] == 0


def test_cancel_confirmed_order_reopens_listing(client, alice, bob, listing, login, db):
    seller, buyer = login(alice.email), login(bob.email)
    offer = make_offer(client, listing.id, buyer).json()
    accepted = client.post(f"{API}/offers/{offer['id']}/accept", headers=seller)
    assert accepted.status_code == 200
    order = client.get(f"{API}/orders", headers=buyer).json()["items"][0]

    cancelled = client.post(f"{API}/orders/{order['id']}/cancel", headers=buyer)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    db.expire_all()
    assert db.get(Listing, listing.id).status == ListingStatus.approved
    assert client.get(f"{API}/offers/{offer['id']}", headers=buyer).json()["status"] == "cancelled"
    assert client.post(f"{API}/orders/{order['id']}/ship", headers=seller).status_code == 409


def test_notification_endpoints_require_authentication(client):
    assert client.get(f"{API}/notifications").status_code == 401
    assert client.get(f"{API}/notifications/unread-count").status_code == 401
    assert client.post(f"{API}/notifications/read-all").status_code == 401


def test_direct_purchase_requires_seller_confirmation_and_persists_delivery(client, alice, bob, carol, listing, login, db):
    seller, buyer, outsider = login(alice.email), login(bob.email), login(carol.email)
    payload = {
        "delivery_name": "Nguyen Van B",
        "delivery_phone": "0912345678",
        "delivery_address": "Cong chinh truong Dai hoc",
        "payment_method": "COD",
        "note": "Gọi trước khi giao",
    }
    created = client.post(f"{API}/listings/{listing.id}/orders", json=payload, headers=buyer)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["status"] == "pending"
    assert data["delivery_phone"] == payload["delivery_phone"]
    assert data["delivery_address"] == payload["delivery_address"]
    assert data["offer_id"] is not None

    duplicate = client.post(f"{API}/listings/{listing.id}/orders", json=payload, headers=outsider)
    assert duplicate.status_code == 409
    assert client.post(f"{API}/orders/{data['id']}/confirm", headers=buyer).status_code == 404
    assert client.post(f"{API}/orders/{data['id']}/confirm", headers=outsider).status_code == 404

    confirmed = client.post(f"{API}/orders/{data['id']}/confirm", headers=seller)
    assert confirmed.status_code == 200 and confirmed.json()["status"] == "confirmed"
    db.expire_all()
    assert db.get(Listing, listing.id).status == ListingStatus.sold

    cancelled = client.post(f"{API}/orders/{data['id']}/cancel", headers=buyer)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"


def test_direct_order_can_be_cancelled_before_confirmation(client, alice, bob, listing, login, db):
    payload = {
        "delivery_name": "Nguyen Van B",
        "delivery_phone": "0912345678",
        "delivery_address": "Cong chinh truong Dai hoc",
        "payment_method": "Gặp trực tiếp",
    }
    created = client.post(f"{API}/listings/{listing.id}/orders", json=payload, headers=login(bob.email))
    assert created.status_code == 201, created.text
    order_id = created.json()["id"]
    cancelled = client.post(f"{API}/orders/{order_id}/cancel", headers=login(bob.email))
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    db.expire_all()
    assert db.get(Listing, listing.id).status == ListingStatus.approved
