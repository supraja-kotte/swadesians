"""Hashing helpers for private browser keys used by equipment listings.

The browser generates a random key and keeps it in localStorage. The server
stores only a SHA-256 digest so a database dump cannot be used to impersonate
an owner or farmer.
"""

import hashlib


def hash_browser_key(value: str) -> str:
    """Return a stable digest of a trimmed browser key."""
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()
