"""Farmer account registration, sign-in, sessions and profile ownership."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import FARMER_COOKIE_NAME
from app.main import app
from app.services.farmer_auth import clear_failed_logins


def _new_username() -> str:
    return f"farmer_{uuid4().hex[:12]}"


def _register(client: TestClient, username: str, password: str = "farmer-pass-123"):
    return client.post(
        "/api/farmer/register",
        json={"username": username, "display_name": "Test Farmer", "password": password},
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_registration_creates_account_and_session() -> None:
    username = _new_username()
    with TestClient(app) as client:
        response = _register(client, username)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["username"] == username
        assert body["display_name"] == "Test Farmer"
        assert body["registered"] is True
        assert body["csrfToken"]
        assert client.cookies.get(FARMER_COOKIE_NAME)

        set_cookie = response.headers.get("set-cookie", "")
        assert "httponly" in set_cookie.lower()

        me = client.get("/api/farmer/me", headers=_bearer(client.cookies.get(FARMER_COOKIE_NAME)))
        assert me.status_code == 200
        assert me.json()["username"] == username


def test_duplicate_registration_is_rejected() -> None:
    username = _new_username()
    with TestClient(app) as client:
        assert _register(client, username).status_code == 200
        duplicate = _register(client, username.upper())
        assert duplicate.status_code == 409


def test_registration_validates_password() -> None:
    with TestClient(app) as client:
        response = _register(client, _new_username(), "short")
        assert response.status_code == 422


def test_login_requires_correct_password() -> None:
    username = _new_username()
    clear_failed_logins()
    try:
        with TestClient(app) as client:
            assert _register(client, username).status_code == 200

            wrong = client.post(
                "/api/farmer/login", json={"username": username, "password": "wrong-password"}
            )
            assert wrong.status_code == 401

            correct = client.post(
                "/api/farmer/login", json={"username": username, "password": "farmer-pass-123"}
            )
            assert correct.status_code == 200
            assert correct.json()["username"] == username
    finally:
        clear_failed_logins()


def test_protected_endpoints_require_farmer_session() -> None:
    with TestClient(app) as client:
        assert client.get("/api/farmer/me").status_code == 401
        assert client.get("/api/farmer/profile").status_code == 401
        assert client.put("/api/farmer/profile", json={}).status_code == 401


def test_farmer_profile_is_private_to_each_account() -> None:
    first_name = _new_username()
    second_name = _new_username()

    with TestClient(app) as first:
        assert _register(first, first_name).status_code == 200
        first_token = first.cookies.get(FARMER_COOKIE_NAME)
        saved = first.put(
            "/api/farmer/profile",
            headers=_bearer(first_token),
            json={"state": "Telangana", "district": "Warangal", "crop": "Paddy", "interests": ["soil"]},
        )
        assert saved.status_code == 200, saved.text
        assert saved.json()["crop"] == "Paddy"

    with TestClient(app) as second:
        assert _register(second, second_name).status_code == 200
        second_token = second.cookies.get(FARMER_COOKIE_NAME)
        other = second.get("/api/farmer/profile", headers=_bearer(second_token))
        assert other.status_code == 200
        assert other.json()["crop"] == ""


def test_cookie_profile_writes_require_csrf() -> None:
    with TestClient(app) as client:
        response = _register(client, _new_username())
        assert response.status_code == 200
        csrf = response.json()["csrfToken"]

        blocked = client.put("/api/farmer/profile", json={"crop": "Paddy"})
        assert blocked.status_code == 403

        allowed = client.put(
            "/api/farmer/profile",
            headers={"X-CSRF-Token": csrf},
            json={"crop": "Paddy"},
        )
        assert allowed.status_code == 200
        assert allowed.json()["crop"] == "Paddy"


def test_logout_invalidates_session() -> None:
    with TestClient(app) as client:
        assert _register(client, _new_username()).status_code == 200
        token = client.cookies.get(FARMER_COOKIE_NAME)

        logout = client.post("/api/farmer/logout", headers=_bearer(token))
        assert logout.status_code == 200
        assert client.get("/api/farmer/me", headers=_bearer(token)).status_code == 401


def test_repeated_failed_logins_are_rate_limited() -> None:
    username = _new_username()
    clear_failed_logins()
    try:
        with TestClient(app) as client:
            assert _register(client, username).status_code == 200
            client.cookies.clear()

            for _ in range(5):
                failed = client.post(
                    "/api/farmer/login", json={"username": username, "password": "wrong-password"}
                )
                assert failed.status_code == 401

            locked = client.post(
                "/api/farmer/login", json={"username": username, "password": "farmer-pass-123"}
            )
            assert locked.status_code == 429
    finally:
        clear_failed_logins()
