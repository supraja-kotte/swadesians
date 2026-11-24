"""Local-only storage for community photos and videos.

Files are written under `config.UPLOAD_DIR` with a generated UUID name and are
served from the same origin at `/uploads/...`. The client never chooses a path,
so directory traversal and look-alike filenames are not possible.

Validation is deliberately strict: extension, declared content type and the
file's magic bytes must agree. A file that fails any check is removed.
"""

import re
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from .. import config

# ext -> (expected content-type prefix, kind, magic bytes at offset 0)
ALLOWED_TYPES = {
    ".jpg": ("image/jpeg", "image", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", "image", b"\xff\xd8\xff"),
    ".png": ("image/png", "image", b"\x89PNG\r\n\x1a\n"),
    ".gif": ("image/gif", "image", b"GIF8"),
    ".webp": ("image/webp", "image", b"RIFF"),
    ".mp4": ("video/mp4", "video", None),
    ".webm": ("video/webm", "video", b"\x1a\x45\xdf\xa3"),
}
CHUNK_SIZE = 64 * 1024
UPLOAD_LIMIT = 10
UPLOAD_WINDOW_SECONDS = 60

_upload_times: defaultdict[str, deque[float]] = defaultdict(deque)


class UploadError(Exception):
    """The file failed validation; the message is shown to the farmer."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class UploadRateLimited(Exception):
    """Too many uploads from one client in the time window."""


def clear_upload_attempts() -> None:
    """Test helper: forget all per-client upload timestamps."""
    _upload_times.clear()


def check_upload_allowed(client_host: str) -> None:
    now = time.monotonic()
    history = _upload_times[client_host or "unknown"]
    while history and now - history[0] > UPLOAD_WINDOW_SECONDS:
        history.popleft()
    if len(history) >= UPLOAD_LIMIT:
        raise UploadRateLimited
    history.append(now)


def _safe_name(filename: str | None) -> str:
    name = Path(filename or "").name
    name = "".join(ch for ch in name if ch.isprintable() and ch not in '\\/:*?"<>|')
    return name[:120] or "upload"


def _magic_ok(ext: str, header: bytes) -> bool:
    magic = ALLOWED_TYPES[ext][2]
    if ext == ".webp":
        return len(header) >= 12 and magic == header[:4] and header[8:12] == b"WEBP"
    if ext == ".mp4":
        return len(header) >= 8 and header[4:8] == b"ftyp"
    return bool(magic and header.startswith(magic))


def _type_ok(ext: str, declared: str | None) -> bool:
    value = (declared or "").split(";", 1)[0].strip().lower()
    if not value or value == "application/octet-stream":
        return True
    expected, kind, _ = ALLOWED_TYPES[ext]
    return value == expected or value.startswith(f"{kind}/")


def save_upload(upload: UploadFile) -> dict[str, str | int]:
    """Validate and store one uploaded file. Returns its public metadata."""
    name = _safe_name(upload.filename)
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise UploadError("type")

    expected, kind, _ = ALLOWED_TYPES[ext]
    if not _type_ok(ext, upload.content_type):
        raise UploadError("type")

    max_bytes = (
        config.UPLOAD_MAX_VIDEO_BYTES if kind == "video" else config.UPLOAD_MAX_IMAGE_BYTES
    )

    now = datetime.now(timezone.utc)
    relative_dir = Path(f"{now.year:04d}") / f"{now.month:02d}"
    target_dir = config.UPLOAD_DIR / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex}{ext}"

    written = 0
    header = b""
    try:
        with target.open("xb") as output:
            while True:
                chunk = upload.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                if len(header) < 16:
                    header += chunk[: 16 - len(header)]
                written += len(chunk)
                if written > max_bytes:
                    raise UploadError("large")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise

    if written == 0 or not _magic_ok(ext, header):
        target.unlink(missing_ok=True)
        raise UploadError("type")

    prefix = config.UPLOAD_URL_PREFIX
    return {
        "path": f"{prefix}/{relative_dir.as_posix()}/{target.name}",
        "kind": kind,
        "name": name,
        "size": written,
    }


def validate_media_ref(path: str, kind: str, name: str) -> bool:
    """Check that a post's media metadata points at one of our stored files."""
    if not path or kind not in ("image", "video") or not name:
        return False

    prefix = config.UPLOAD_URL_PREFIX + "/"
    if not path.startswith(prefix):
        return False
    relative = path[len(prefix) :]
    if not relative or ".." in relative or any(ch in relative for ch in '\\?#'):
        return False

    try:
        candidate = (config.UPLOAD_DIR / relative).resolve()
        candidate.relative_to(config.UPLOAD_DIR)
    except (ValueError, OSError):
        return False

    if not candidate.is_file():
        return False
    ext = candidate.suffix.lower()
    stored = ALLOWED_TYPES.get(ext)
    return bool(stored and stored[1] == kind and re.fullmatch(r"[A-Za-z0-9._-]{32}\.[a-z0-9]+", candidate.name))
