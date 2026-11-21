"""Tests for local community photo/video uploads and post attachments."""

from fastapi.testclient import TestClient

from app import config
from app.main import app
from app.services import uploads

client = TestClient(app)

PNG = b"\x89PNG\r\n\x1a\n" + b"not-a-real-image-but-has-the-header"
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"not-a-real-video-but-has-the-header"


def _upload(filename: str, content: bytes, content_type: str):
    return client.post(
        "/api/community/upload",
        files={"file": (filename, content, content_type)},
    )


def _post(title: str, media: dict | None = None):
    payload = {
        "author": "Media farmer",
        "language": "en",
        "category": "crops",
        "title": title,
        "body": "A caption with enough detail.",
    }
    if media:
        # The upload response uses short keys; the post payload uses media_*.
        payload.update(
            {
                "media_path": media["path"],
                "media_kind": media["kind"],
                "media_name": media["name"],
            }
        )
    return client.post("/api/community/posts", json=payload)


def test_upload_image_is_stored_and_served() -> None:
    uploads.clear_upload_attempts()
    response = _upload("my field.png", PNG, "image/png")
    assert response.status_code == 200

    meta = response.json()
    assert meta["kind"] == "image"
    assert meta["name"] == "my field.png"
    assert meta["size"] == len(PNG)
    assert meta["path"].startswith(f"{config.UPLOAD_URL_PREFIX}/20")

    served = client.get(meta["path"])
    assert served.status_code == 200
    assert served.content == PNG
    csp = served.headers["content-security-policy"]
    assert "img-src 'self' data: blob:" in csp
    assert "media-src 'self' blob:" in csp


def test_upload_video_is_accepted() -> None:
    uploads.clear_upload_attempts()
    response = _upload("field.mp4", MP4, "video/mp4")
    assert response.status_code == 200
    assert response.json()["kind"] == "video"


def test_upload_rejects_disallowed_type_and_fake_magic_bytes() -> None:
    uploads.clear_upload_attempts()
    assert _upload("notes.txt", b"hello", "text/plain").status_code == 415
    assert _upload("bad.png", b"not a png", "image/png").status_code == 415
    assert _upload("evil.png", PNG, "text/html").status_code == 415

    uploads.clear_upload_attempts()
    assert uploads.validate_media_ref("https://example.com/x.png", "image", "x.png") is False
    assert uploads.validate_media_ref("/uploads/../secret.png", "image", "x.png") is False


def test_upload_rejects_oversized_file(monkeypatch) -> None:
    uploads.clear_upload_attempts()
    monkeypatch.setattr(config, "UPLOAD_MAX_IMAGE_BYTES", 16)
    assert _upload("big.png", PNG, "image/png").status_code == 413


def test_upload_rate_limit(monkeypatch) -> None:
    uploads.clear_upload_attempts()
    monkeypatch.setattr(uploads, "UPLOAD_LIMIT", 1)
    assert _upload("one.png", PNG, "image/png").status_code == 200
    assert _upload("two.png", PNG, "image/png").status_code == 429
    monkeypatch.setattr(uploads, "UPLOAD_LIMIT", 10)
    uploads.clear_upload_attempts()


def test_post_with_media_is_serialized_everywhere() -> None:
    uploads.clear_upload_attempts()
    meta = _upload("crop.png", PNG, "image/png").json()
    created = _post("My tomato crop", meta)
    assert created.status_code == 201

    media = created.json()["media"]
    assert media == {"path": meta["path"], "kind": "image", "name": "crop.png"}

    post_id = created.json()["id"]
    detail = client.get(f"/api/community/posts/{post_id}")
    assert detail.json()["post"]["media"] == media

    listing = client.get("/api/community/posts").json()["posts"]
    assert next(item for item in listing if item["id"] == post_id)["media"] == media


def test_invalid_media_reference_is_rejected() -> None:
    uploads.clear_upload_attempts()
    response = _post("Invalid link", {"path": "/etc/passwd", "kind": "image", "name": "x.png"})
    assert response.status_code == 422

    partial = client.post(
        "/api/community/posts",
        json={"title": "Partial link", "body": "A caption with enough detail.", "media_kind": "image"},
    )
    assert partial.status_code == 422
