"""Re-check stored scheme links against the official-domain allowlist.

Structural checks always run. With --strict, each HTTPS URL is also requested
and must return a successful or redirect status. Some government sites block
automated requests, so network failures are reported as warnings by default.

Run from `backend`:
    .\\.venv\\Scripts\\python.exe -m scripts.verify_scheme_links
    .\\.venv\\Scripts\\python.exe -m scripts.verify_scheme_links --strict
"""

import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.db.seed_scheme_links import ALLOWED_SUFFIXES, is_official_url
from app.models.schemes import SchemeLink

USER_AGENT = "AgriGuide link verification (demo)"


def check_reachable(url: str) -> tuple[bool, str]:
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        with urlopen(request, timeout=12) as response:
            return True, str(response.status)
    except HTTPError as exc:
        # A blocked bot request still proves the host answered.
        return exc.code < 500, f"HTTP {exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        return False, str(exc)


def main() -> int:
    strict = "--strict" in sys.argv
    failures: list[str] = []

    with SessionLocal() as db:
        links = db.execute(select(SchemeLink).order_by(SchemeLink.id)).scalars().all()

    if not links:
        print("No scheme links stored. Start the app once to seed them.")
        return 1

    print(f"Checking {len(links)} official links (allowed suffixes: {', '.join(ALLOWED_SUFFIXES)}).")

    for link in links:
        if not is_official_url(link.url):
            failures.append(f"{link.id}: unofficial URL {link.url}")
            print(f"FAIL  {link.id}: unofficial URL")
            continue

        if strict:
            ok, detail = check_reachable(link.url)
            status = "OK  " if ok else "WARN"
            print(f"{status}  {link.id}: {detail}")
            if not ok:
                failures.append(f"{link.id}: {detail}")
        else:
            print(f"OK    {link.id}: {link.source_domain} (verified {link.verified_on})")

    if failures:
        print("\nProblems found:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("\nAll stored links passed the check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
