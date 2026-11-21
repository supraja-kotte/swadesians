"""Tests for community posts, replies, reports and moderation."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_community_starts_without_demo_posts() -> None:
    response = client.get("/api/community/posts")

    assert response.status_code == 200
    posts = response.json()["posts"]
    assert all(post["is_demo"] is False for post in posts)


def test_post_reply_and_report_flow() -> None:
    created = client.post(
        "/api/community/posts",
        json={
            "author": "Test farmer",
            "language": "en",
            "category": "general",
            "title": "A test question about irrigation",
            "body": "This is a test question body used by the automated test suite.",
        },
    )
    assert created.status_code == 201
    post_id = created.json()["id"]
    assert created.json()["is_demo"] is False

    reply = client.post(
        f"/api/community/posts/{post_id}/replies",
        json={"author": "Test neighbour", "language": "en", "body": "A helpful test reply."},
    )
    assert reply.status_code == 201
    reply_id = reply.json()["id"]

    detail = client.get(f"/api/community/posts/{post_id}")
    assert detail.status_code == 200
    assert detail.json()["post"]["reply_count"] == 1
    assert detail.json()["replies"][0]["id"] == reply_id

    reported = client.post(f"/api/community/posts/{post_id}/report")
    assert reported.json()["reports"] == 1

    reply_report = client.post(f"/api/community/replies/{reply_id}/report")
    assert reply_report.json()["reports"] == 1


def test_moderation_hides_content(admin_headers: dict[str, str]) -> None:
    created = client.post(
        "/api/community/posts",
        json={
            "author": "",
            "language": "en",
            "category": "general",
            "title": "Moderation test question",
            "body": "This post is created only to verify hiding and restoring.",
        },
    )
    post_id = created.json()["id"]
    assert created.json()["author"] == "Farmer"

    hidden = client.patch(
        f"/api/community/posts/{post_id}/status",
        json={"status": "hidden"},
        headers=admin_headers,
    )
    assert hidden.json()["status"] == "hidden"

    listed_ids = [post["id"] for post in client.get("/api/community/posts").json()["posts"]]
    assert post_id not in listed_ids
    assert client.get(f"/api/community/posts/{post_id}").status_code == 404

    review_ids = [
        post["id"]
        for post in client.get(
            "/api/community/posts?include_hidden=true", headers=admin_headers
        ).json()["posts"]
    ]
    assert post_id in review_ids

    restored = client.patch(
        f"/api/community/posts/{post_id}/status",
        json={"status": "published"},
        headers=admin_headers,
    )
    assert restored.json()["status"] == "published"
    assert client.get(f"/api/community/posts/{post_id}").status_code == 200


def test_validation_and_category_filter() -> None:
    too_short = client.post(
        "/api/community/posts",
        json={"category": "general", "title": "hi", "body": "ok"},
    )
    assert too_short.status_code == 422

    bad_category = client.post(
        "/api/community/posts",
        json={"category": "unknown", "title": "A valid length title", "body": "A valid body text"},
    )
    assert bad_category.status_code == 422

    created = client.post(
        "/api/community/posts",
        json={
            "author": "Test farmer",
            "language": "en",
            "category": "weather",
            "title": "A real question about monsoon planning",
            "body": "This post is created by the test suite to verify category filtering.",
        },
    )
    assert created.status_code == 201

    filtered = client.get("/api/community/posts?category=weather").json()["posts"]
    assert filtered
    assert all(post["category"] == "weather" for post in filtered)
