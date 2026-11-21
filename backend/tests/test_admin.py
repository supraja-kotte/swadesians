"""Tests for administrator sign-in and access control."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import hash_password, verify_password

client = TestClient(app)


def _login(
    username: str = "testadmin",
    password: str = "test-password-12345",
    test_client: TestClient | None = None,
):
    target = test_client or TestClient(app)
    return target.post("/api/admin/login", json={"username": username, "password": password})


def test_login_success_and_failure() -> None:
    success = _login()
    assert success.status_code == 200
    body = success.json()
    assert body["username"] == "testadmin"
    assert len(body["csrfToken"]) >= 24
    assert "expires_at" in body
    assert success.cookies.get("agriguide_admin")
    assert "httponly" in success.headers["set-cookie"].lower()

    assert _login(password="wrong-password-123").status_code == 401
    assert _login(username="unknown-admin").status_code == 401


def test_protected_endpoints_require_a_token() -> None:
    for path in ("/api/admin/me", "/api/admin/reports", "/api/admin/queue"):
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"Authorization": "Bearer bad-token"}).status_code == 401


def test_me_and_moderation_with_token(admin_headers: dict[str, str]) -> None:
    assert client.get("/api/admin/me", headers=admin_headers).json()["username"] == "testadmin"

    reports = client.get("/api/admin/reports", headers=admin_headers)
    assert reports.status_code == 200
    assert "posts" in reports.json() and "replies" in reports.json()

    queue = client.get("/api/admin/queue", headers=admin_headers)
    assert queue.status_code == 200
    assert "posts" in queue.json() and "replies" in queue.json()


def test_hidden_content_requires_admin(admin_headers: dict[str, str]) -> None:
    assert client.get("/api/community/posts?include_hidden=true").status_code == 401
    assert client.get(
        "/api/community/posts?include_hidden=true", headers=admin_headers
    ).status_code == 200


def test_moderation_without_token_is_rejected() -> None:
    created = client.post(
        "/api/community/posts",
        json={
            "author": "Farmer",
            "language": "en",
            "category": "general",
            "title": "Access control check question",
            "body": "This post exists to verify that moderation needs a token.",
        },
    )
    post_id = created.json()["id"]
    response = client.patch(
        f"/api/community/posts/{post_id}/status", json={"status": "hidden"}
    )
    assert response.status_code == 401


def test_logout_invalidates_the_token() -> None:
    local_client = TestClient(app)
    login = _login(test_client=local_client)
    token = login.cookies.get("agriguide_admin")
    assert token
    headers = {"Authorization": f"Bearer {token}"}
    assert local_client.get("/api/admin/me", headers=headers).status_code == 200

    assert local_client.post("/api/admin/logout", headers=headers).status_code == 200
    assert local_client.get("/api/admin/me", headers=headers).status_code == 401


def test_password_hashing_is_salted_and_not_plain_text() -> None:
    first_hash, first_salt = hash_password("a-strong-password")
    second_hash, second_salt = hash_password("a-strong-password")

    assert first_hash != second_hash
    assert first_salt != second_salt
    assert "a-strong-password" not in first_hash
    assert verify_password("a-strong-password", first_hash, first_salt) is True
    assert verify_password("wrong-password", first_hash, first_salt) is False


def test_repeated_failed_logins_are_rate_limited() -> None:
    from app.services.auth import clear_failed_logins

    clear_failed_logins()
    for _ in range(5):
        assert _login(password="wrong-password-123").status_code == 401

    blocked = _login()
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    clear_failed_logins()


def test_cookie_auth_requires_csrf_for_moderation() -> None:
    local_client = TestClient(app)
    created = local_client.post(
        "/api/community/posts",
        json={
            "author": "Cookie check farmer",
            "language": "en",
            "category": "general",
            "title": "Cookie and CSRF check question",
            "body": "This post checks that cookie-based moderation needs a CSRF header.",
        },
    )
    post_id = created.json()["id"]

    login = _login(test_client=local_client)
    csrf_token = login.json()["csrfToken"]
    assert local_client.get("/api/admin/me").status_code == 200
    assert local_client.get("/api/community/posts?include_hidden=true").status_code == 200

    blocked = local_client.patch(
        f"/api/community/posts/{post_id}/status", json={"status": "hidden"}
    )
    assert blocked.status_code == 403

    allowed = local_client.patch(
        f"/api/community/posts/{post_id}/status",
        json={"status": "hidden"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert allowed.status_code == 200

    logout = local_client.post(
        "/api/admin/logout", headers={"X-CSRF-Token": csrf_token}
    )
    assert logout.status_code == 200
    assert local_client.get("/api/admin/me").status_code == 401
