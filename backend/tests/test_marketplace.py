"""Tests for demo marketplace listings and buyer enquiries."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.marketplace import VALID_MARKETPLACE_CATEGORIES

client = TestClient(app)


def test_demo_listings_are_labelled_without_prices() -> None:
    response = client.get("/api/marketplace/listings")

    assert response.status_code == 200
    listings = response.json()["listings"]
    assert len(listings) >= 8
    assert all(item["is_demo"] is True for item in listings)
    assert all(item["price_amount"] is None for item in listings)
    assert all(item["category"] in VALID_MARKETPLACE_CATEGORIES for item in listings)


def test_category_and_location_filters() -> None:
    vegetables = client.get("/api/marketplace/listings?category=vegetables").json()["listings"]
    assert vegetables
    assert all(item["category"] == "vegetables" for item in vegetables)

    guntur = client.get("/api/marketplace/listings?location=Guntur").json()["listings"]
    assert guntur
    assert all(item["district"] == "Guntur" for item in guntur)


def test_enquiry_flow() -> None:
    enquiry = client.post(
        "/api/marketplace/listings/demo-marketplace-1/enquiries",
        json={
            "name": "Test buyer",
            "phone": "9876543210",
            "quantity": "2 quintals",
            "message": "Interested in demo produce",
        },
    )

    assert enquiry.status_code == 201
    body = enquiry.json()
    assert body["status"] == "new"
    assert body["is_demo"] is True
    assert "No real seller" in body["note"]


def test_enquiry_validation_and_missing_listing() -> None:
    bad_phone = client.post(
        "/api/marketplace/listings/demo-marketplace-1/enquiries",
        json={"name": "Test buyer", "phone": "12"},
    )
    assert bad_phone.status_code == 422

    missing = client.post(
        "/api/marketplace/listings/not-a-listing/enquiries",
        json={"name": "Test buyer", "phone": "9876543210"},
    )
    assert missing.status_code == 404

    bad_category = client.get("/api/marketplace/listings?category=unknown")
    assert bad_category.status_code == 422
