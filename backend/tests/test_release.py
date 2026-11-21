"""Release-readiness checks: headers, safe defaults and no leaked secrets."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".venv", "__pycache__", ".pytest_cache", "_checkpoints", "node_modules"}
TEXT_SUFFIXES = {".py", ".js", ".html", ".css", ".md", ".json"}
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(?:ai|youtube|api)[_-]?key\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),
]


def _text_files(base: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in base.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            files.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return files


def test_security_headers_are_added_to_api_and_static_pages() -> None:
    for path in ("/api/health", "/"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert "geolocation=(self)" in response.headers["permissions-policy"]


def test_cors_rejects_an_unlisted_origin() -> None:
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_frontend_contains_no_api_keys() -> None:
    leaked = [
        str(path.relative_to(ROOT))
        for path, text in _text_files(ROOT / "frontend")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS)
    ]
    assert leaked == []


def test_runtime_code_has_no_removed_crop_doctor_feature() -> None:
    found = []
    for base in (ROOT / "frontend", ROOT / "backend" / "app"):
        for path, text in _text_files(base):
            if "crop doctor" in text.lower():
                found.append(str(path.relative_to(ROOT)))
    assert found == []


def test_demo_release_version_is_visible() -> None:
    response = client.get("/api/health")
    assert response.json()["version"].endswith("-demo")
