"""Run the checks that must pass before sharing a demo release.

From `agri-guide/backend`:
    .\\.venv\\Scripts\\python.exe -m scripts.release_check

This is a convenience wrapper. The automated pytest suite is the source of
truth; this script also scans runtime code for accidental secrets and removed
features.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".venv", "__pycache__", ".pytest_cache", "_checkpoints", "node_modules"}
TEXT_SUFFIXES = {".py", ".js", ".html", ".css", ".md", ".json"}
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(?:ai|youtube|api)[_-]?key\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),
]


def _text_files(base: Path):
    for path in base.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue


def _scan() -> list[str]:
    problems: list[str] = []

    for path, text in _text_files(ROOT / "frontend"):
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            problems.append(f"Possible secret in {path.relative_to(ROOT)}")

    for base in (ROOT / "frontend", ROOT / "backend" / "app"):
        for path, text in _text_files(base):
            if "crop doctor" in text.lower():
                problems.append(f"Removed feature still present in {path.relative_to(ROOT)}")

    return problems


def main() -> None:
    problems = _scan()
    for problem in problems:
        print(f"FAIL: {problem}")

    print("Running pytest...")
    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
    )
    print(tests.stdout.strip())
    if tests.stderr.strip():
        print(tests.stderr.strip())

    if problems or tests.returncode != 0:
        print("Release check FAILED.")
        raise SystemExit(1)

    print("Release check passed.")


if __name__ == "__main__":
    main()
