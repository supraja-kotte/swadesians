"""Generate a native-speaker review sheet from the frontend i18n files.

No translation is marked as reviewed. A human reviewer edits this generated
file and changes the status column only after checking the wording.

Run from `agri-guide/backend`:
    .\\.venv\\Scripts\\python.exe -m scripts.translation_review
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
I18N_DIR = ROOT / "frontend" / "src" / "i18n"
OUTPUT = ROOT / "docs" / "TRANSLATION_REVIEW.md"
LANGUAGES = ["en", "te", "hi", "ta", "mr"]
LANGUAGE_NAMES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "mr": "Marathi",
}

LANG_OBJECT = re.compile(r"^\s*(en|te|hi|ta|mr):\s*\{")
LANG_EXPORT = re.compile(r"^\s*export const (en|te|hi|ta|mr)\s*=")
ENTRY = re.compile(r'^\s*([A-Za-z0-9_]+):\s*"((?:[^"\\]|\\.)*)"')


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def collect() -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for path in sorted(I18N_DIR.glob("*.js")):
        current = None
        for line in path.read_text(encoding="utf-8").splitlines():
            lang_match = LANG_OBJECT.match(line) or LANG_EXPORT.match(line)
            if lang_match:
                current = lang_match.group(1)
                continue
            entry_match = ENTRY.match(line)
            if entry_match and current:
                key, value = entry_match.groups()
                entries.setdefault(key, {})[current] = value
    return entries


def main() -> None:
    entries = collect()
    lines = [
        "# Native-speaker translation review sheet",
        "",
        "**Status: PENDING.** This file is generated from the current frontend strings.",
        "No wording below has been human-reviewed. A reviewer should correct the",
        "target-language cells and change `PENDING` to `APPROVED` with a date.",
        "",
        "| Key | English source | Telugu | Hindi | Tamil | Marathi | Status |",
        "|---|---|---|---|---|---|---|",
    ]

    for key in sorted(entries):
        values = entries[key]
        cells = [_cell(values.get(lang, "")) for lang in LANGUAGES]
        lines.append(f"| `{key}` | " + " | ".join(cells) + " | PENDING |")

    lines.extend(
        [
            "",
            f"Total keys found: {len(entries)}",
            "",
            "## Reviewer sign-off",
            "",
            "- Telugu: ____________________  Date: __________",
            "- Hindi: ____________________  Date: __________",
            "- Tamil: ____________________  Date: __________",
            "- Marathi: ____________________  Date: __________",
            "",
        ]
    )

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(entries)} keys.")


if __name__ == "__main__":
    main()
