"""Shared test setup.

Tests use an isolated temporary SQLite file so they never touch the real
development database. A plain TestClient also skips the app's startup event,
so we create the tables, non-demo reference content and one test administrator here.
"""

import os
import tempfile

_db_file = tempfile.NamedTemporaryFile(prefix="agriguide-test-", suffix=".db", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"

# Uploads go to a temporary folder so tests never touch the local media store.
_upload_dir = tempfile.mkdtemp(prefix="agriguide-uploads-")
os.environ["UPLOAD_DIR"] = _upload_dir

import pytest  # noqa: E402

from app.db.connection import init_db  # noqa: E402

TEST_ADMIN = ("testadmin", "test-password-12345")


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> None:
    init_db()

    from app.services.auth import clear_failed_logins, create_admin

    clear_failed_logins()
    try:
        create_admin(*TEST_ADMIN)
    except ValueError:
        # Already created by an earlier fixture in the same process.
        pass

    yield
    try:
        os.unlink(_db_file.name)
    except OSError:
        pass
    import shutil

    shutil.rmtree(_upload_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def admin_headers() -> dict[str, str]:
    from fastapi.testclient import TestClient

    from app.main import app

    response = TestClient(app).post(
        "/api/admin/login",
        json={"username": TEST_ADMIN[0], "password": TEST_ADMIN[1]},
    )
    assert response.status_code == 200
    token = response.cookies.get("agriguide_admin")
    assert token
    return {"Authorization": f"Bearer {token}"}
