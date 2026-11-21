"""Create one administrator account.

Run from the backend folder:
    .\\.venv\\Scripts\\python.exe -m scripts.create_admin

You can avoid interactive prompts by exporting ADMIN_USERNAME and ADMIN_PASSWORD
in your shell before running this command. The password is never written to the
database in plain text.

Usage: python -m scripts.create_admin
"""

import getpass
import os
import sys

from app.db.connection import init_db
from app.services.auth import create_admin


def main() -> None:
    init_db()

    username = os.environ.get("ADMIN_USERNAME", "").strip()
    if not username:
        username = input("Admin username: ").strip()

    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        password = getpass.getpass("Admin password (at least 12 characters): ")
        if password != getpass.getpass("Confirm password: "):
            print("Passwords do not match.", file=sys.stderr)
            raise SystemExit(1)

    try:
        admin = create_admin(username, password)
    except ValueError as exc:
        print(f"Could not create administrator: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Created administrator '{admin.username}'.")
    print("Sign in at http://127.0.0.1:8000/#/admin")


if __name__ == "__main__":
    main()
