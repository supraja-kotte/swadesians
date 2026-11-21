"""Tests for demo equipment listings and enquiries."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.equipment import VALID_EQUIPMENT_CATEGORIES

client = TestClient(app)


def test_demo_listings_are_labelled_without_prices() -> None:
    response = client.get("/api/equipment/listings")

    assert response.status_code == 200
    listings = response.json()["listings"]
    assert len(listings) >= 7
    assert all(item["is_demo"] is True for item in listings)
    assert all(item["price_amount"] is None for item in listings)
    assert all(item["category"] in VALID_EQUIPMENT_CATEGORIES for item in listings)


def test_category_and_location_filters() -> None:
    tillage = client.get("/api/equipment/listings?category=tillage").json()["listings"]
    assert tillage
    assert all(item["category"] == "tillage" for item in tillage)

    guntur = client.get("/api/equipment/listings?location=Guntur").json()["listings"]
    assert len(guntur) == 1
    assert guntur[0]["district"] == "Guntur"


def test_enquiry_flow() -> None:
    enquiry = client.post(
        "/api/equipment/listings/demo-equipment-1/enquiries",
        json={"name": "Test farmer", "phone": "9876543210", "message": "Interested in demo listing"},
    )

    assert enquiry.status_code == 201
    body = enquiry.json()
    assert body["status"] == "new"
    assert body["is_demo"] is True
    assert "No real provider" in body["note"]


def test_enquiry_validation_and_missing_listing() -> None:
    bad_phone = client.post(
        "/api/equipment/listings/demo-equipment-1/enquiries",
        json={"name": "Test farmer", "phone": "12"},
    )
    assert bad_phone.status_code == 422

    missing = client.post(
        "/api/equipment/listings/not-a-listing/enquiries",
        json={"name": "Test farmer", "phone": "9876543210"},
    )
    assert missing.status_code == 404

    bad_category = client.get("/api/equipment/listings?category=unknown")
    assert bad_category.status_code == 422
