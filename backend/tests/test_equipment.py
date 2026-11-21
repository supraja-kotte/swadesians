"""Tests for owner-submitted equipment listings and the rental enquiry flow."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def owner_headers() -> dict[str, str]:
    return {"X-Owner-Key": uuid4().hex}


def farmer_key() -> str:
    return uuid4().hex


def create_listing(owner_key: str, **overrides) -> dict:
    payload = {
        "category": "tractors",
        "title": "Owner submitted tractor",
        "description": "Owner-provided description",
        "state": "Andhra Pradesh",
        "district": "Guntur",
        "price_amount": 2500,
        "price_unit": "day",
        "owner_label": "Verified by owner",
        "owner_contact": "owner@example.in",
        "availability": "Weekdays",
        "owner_key": owner_key,
    }
    payload.update(overrides)
    response = client.post("/api/equipment/listings", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def public_ids() -> set[str]:
    response = client.get("/api/equipment/listings", params={"limit": 100})
    assert response.status_code == 200
    return {item["id"] for item in response.json()["listings"]}


def test_owner_submitted_listings_are_real_data_not_demo() -> None:
    key = uuid4().hex
    listing = create_listing(key)

    assert listing["is_demo"] is False
    assert listing["status"] == "active"
    assert listing["price_amount"] == 2500
    assert listing["availability"] == "Weekdays"

    public = client.get("/api/equipment/listings").json()["listings"]
    assert all(item["is_demo"] is False for item in public)
    assert all(item["price_amount"] is not None for item in public)
    assert all("owner_contact" not in item for item in public)

    by_category = client.get("/api/equipment/listings?category=tractors").json()["listings"]
    assert listing["id"] in {item["id"] for item in by_category}

    by_place = client.get("/api/equipment/listings?location=Guntur").json()["listings"]
    assert listing["id"] in {item["id"] for item in by_place}

    bad_category = client.get("/api/equipment/listings?category=unknown")
    assert bad_category.status_code == 422

    bad_price = client.post(
        "/api/equipment/listings",
        json={
            "category": "tractors",
            "title": "Invalid price",
            "state": "Andhra Pradesh",
            "district": "Guntur",
            "price_amount": 0,
            "price_unit": "day",
            "owner_label": "Owner",
            "owner_contact": "owner@example.in",
            "owner_key": key,
        },
    )
    assert bad_price.status_code == 422


def test_full_enquiry_flow_connects_farmer_and_owner(admin_headers: dict[str, str]) -> None:
    owner_key = uuid4().hex
    key = farmer_key()
    listing = create_listing(owner_key)

    enquiry = client.post(
        f"/api/equipment/listings/{listing['id']}/enquiries",
        json={
            "name": "Test farmer",
            "phone": "9876543210",
            "message": "Need it on Friday",
            "farmer_key": key,
        },
    )
    assert enquiry.status_code == 201, enquiry.text
    body = enquiry.json()
    assert body["status"] == "new"
    assert body["owner_label"] == "Verified by owner"
    assert body["owner_contact"] == "owner@example.in"
    assert body["listing_title"] == listing["title"]

    mine = client.get("/api/equipment/owner/listings", headers={"X-Owner-Key": owner_key})
    assert mine.status_code == 200
    own_listing = next(item for item in mine.json()["listings"] if item["id"] == listing["id"])
    assert own_listing["new_enquiries"] == 1
    assert own_listing["owner_contact"] == "owner@example.in"

    owner_enquiries = client.get(
        "/api/equipment/owner/enquiries", headers={"X-Owner-Key": owner_key}
    )
    assert owner_enquiries.status_code == 200
    owner_row = next(
        item for item in owner_enquiries.json()["enquiries"] if item["id"] == body["id"]
    )
    assert owner_row["farmer_name"] == "Test farmer"
    assert owner_row["farmer_phone"] == "9876543210"
    assert owner_row["message"] == "Need it on Friday"

    farmer_enquiries = client.get(
        "/api/equipment/farmer/enquiries", headers={"X-Farmer-Key": key}
    )
    assert farmer_enquiries.status_code == 200
    farmer_row = next(
        item for item in farmer_enquiries.json()["enquiries"] if item["id"] == body["id"]
    )
    assert farmer_row["owner_contact"] == "owner@example.in"
    assert farmer_row["owner_reply"] == ""

    updated = client.patch(
        f"/api/equipment/owner/enquiries/{body['id']}",
        headers={"X-Owner-Key": owner_key},
        json={"status": "contacted", "reply": "Called the farmer."},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "contacted"

    after_reply = client.get(
        "/api/equipment/farmer/enquiries", headers={"X-Farmer-Key": key}
    ).json()["enquiries"]
    replied = next(item for item in after_reply if item["id"] == body["id"])
    assert replied["status"] == "contacted"
    assert replied["owner_reply"] == "Called the farmer."

    admin_rows = client.get("/api/admin/equipment/enquiries", headers=admin_headers).json()
    admin_row = next(item for item in admin_rows["enquiries"] if item["id"] == body["id"])
    assert admin_row["farmer_phone"] == "9876543210"
    assert admin_row["owner_contact"] == "owner@example.in"

    other_owner = client.patch(
        f"/api/equipment/owner/enquiries/{body['id']}",
        headers=owner_headers(),
        json={"status": "closed"},
    )
    assert other_owner.status_code == 404


def test_owner_pause_and_admin_hide_control_public_visibility(
    admin_headers: dict[str, str],
) -> None:
    owner_key = uuid4().hex
    listing = create_listing(owner_key)

    paused = client.patch(
        f"/api/equipment/owner/listings/{listing['id']}",
        headers={"X-Owner-Key": owner_key},
        json={"status": "paused"},
    )
    assert paused.status_code == 200
    assert listing["id"] not in public_ids()

    resumed = client.patch(
        f"/api/equipment/owner/listings/{listing['id']}",
        headers={"X-Owner-Key": owner_key},
        json={"status": "active", "availability": "Any day"},
    )
    assert resumed.status_code == 200
    assert resumed.json()["availability"] == "Any day"
    assert listing["id"] in public_ids()

    hidden = client.patch(
        f"/api/admin/equipment/listings/{listing['id']}",
        headers=admin_headers,
        json={"status": "hidden"},
    )
    assert hidden.status_code == 200
    assert listing["id"] not in public_ids()

    owner_attempt = client.patch(
        f"/api/equipment/owner/listings/{listing['id']}",
        headers={"X-Owner-Key": owner_key},
        json={"status": "active"},
    )
    assert owner_attempt.status_code == 403

    restored = client.patch(
        f"/api/admin/equipment/listings/{listing['id']}",
        headers=admin_headers,
        json={"status": "active"},
    )
    assert restored.status_code == 200
    assert listing["id"] in public_ids()


def test_enquiry_validation_and_ownership_checks() -> None:
    owner_key = uuid4().hex
    listing = create_listing(owner_key)

    bad_phone = client.post(
        f"/api/equipment/listings/{listing['id']}/enquiries",
        json={"name": "Test farmer", "phone": "12", "farmer_key": farmer_key()},
    )
    assert bad_phone.status_code == 422

    missing_key = client.post(
        f"/api/equipment/listings/{listing['id']}/enquiries",
        json={"name": "Test farmer", "phone": "9876543210"},
    )
    assert missing_key.status_code == 422

    missing_listing = client.post(
        "/api/equipment/listings/not-a-listing/enquiries",
        json={"name": "Test farmer", "phone": "9876543210", "farmer_key": farmer_key()},
    )
    assert missing_listing.status_code == 404

    wrong_owner = client.patch(
        f"/api/equipment/owner/listings/{listing['id']}",
        headers=owner_headers(),
        json={"title": "Someone else's edit"},
    )
    assert wrong_owner.status_code == 404

    short_key = client.get("/api/equipment/owner/listings", headers={"X-Owner-Key": "short"})
    assert short_key.status_code == 422
