"""Officially verified government scheme links.

Verification policy
-------------------
* Only official government domains are stored (gov.in and state government
  domains). Each URL was opened and checked on 2026-11-21.
* Scheme names are proper nouns. No benefit amount, eligibility rule,
  application promise or translated scheme fact is stored here.
* A link is a pointer to the official source, not an endorsement or a claim
  that the scheme is currently open. The official page is always authoritative.
* Entries must be re-verified before each release; `verified_on` makes stale
  entries visible.

Run `python -m scripts.verify_scheme_links` to re-check the stored URLs.
"""

from sqlalchemy import select
from urllib.parse import urlparse

from app.db.connection import SessionLocal
from app.models.schemes import SchemeLink

VERIFIED_ON = "2026-11-21"

ALLOWED_SUFFIXES = ("gov.in", "nic.in")

# (id, name, level, state, url, sort_order)
VERIFIED_LINKS: list[tuple[str, str, str, str | None, str, int]] = [
    # Central government
    (
        "pm-kisan",
        "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "central",
        None,
        "https://pmkisan.gov.in/",
        1,
    ),
    (
        "pmfby",
        "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "central",
        None,
        "https://pmfby.gov.in/",
        1,
    ),
    (
        "enam",
        "e-National Agriculture Market (eNAM)",
        "central",
        None,
        "https://enam.gov.in/",
        1,
    ),
    (
        "soil-health-card",
        "Soil Health Card",
        "central",
        None,
        "https://soilhealth.dac.gov.in/",
        1,
    ),
    (
        "agri-infrastructure-fund",
        "Agriculture Infrastructure Fund (AIF)",
        "central",
        None,
        "https://agriinfra.dac.gov.in/",
        1,
    ),
    (
        "natural-farming",
        "National Mission on Natural Farming (NMNF)",
        "central",
        None,
        "https://naturalfarming.dac.gov.in/Schemes",
        1,
    ),
    (
        "nmsa",
        "National Mission on Sustainable Agriculture (NMSA)",
        "central",
        None,
        "https://nmsa.dac.gov.in/",
        1,
    ),
    (
        "digital-india-pm-kisan",
        "PM-KISAN on the Digital India portal",
        "central",
        None,
        "https://www.digitalindia.gov.in/initiative/pm-kisan",
        1,
    ),
    (
        "india-gov-pm-kisan",
        "PM-KISAN registration — National Portal of India",
        "central",
        None,
        "https://www.india.gov.in/services/details/register-as-a-new-farmer-for-pradhan-mantri-kisan-samman-nidhi-pm-kisan",
        1,
    ),
    # Andhra Pradesh
    (
        "ap-annadata-sukhibhava",
        "Annadata Sukhibhava – PM KISAN",
        "state",
        "Andhra Pradesh",
        "https://annadathasukhibhava.ap.gov.in/",
        2,
    ),
    (
        "ap-ysr-rytu-bharosa",
        "YSR Rythu Bharosa (district agriculture information)",
        "state",
        "Andhra Pradesh",
        "https://spsnellore.ap.gov.in/agriculture",
        2,
    ),
    # Telangana
    (
        "ts-rythu-bharosa",
        "Rythu Bharosa and Rythu Bima state farmer portal",
        "state",
        "Telangana",
        "https://www.rythubharosa.telangana.gov.in/Default_Home.aspx",
        2,
    ),
    (
        "ts-government-initiatives",
        "Telangana Government Initiatives",
        "state",
        "Telangana",
        "https://www.telangana.gov.in/government-initiatives",
        2,
    ),
]


def is_official_url(url: str) -> bool:
    """Allow only HTTPS URLs on Indian government domains."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and any(
        host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_SUFFIXES
    )


def seed_verified_scheme_links() -> None:
    """Insert verified links once. Existing rows are never silently replaced."""
    with SessionLocal() as db:
        existing = db.execute(select(SchemeLink.id).limit(1)).first()
        if existing:
            return

        for link_id, name, level, state, url, sort_order in VERIFIED_LINKS:
            if not is_official_url(url):
                raise ValueError(f"Refusing to seed an unofficial URL: {url}")

            parsed = urlparse(url)
            db.add(
                SchemeLink(
                    id=link_id,
                    name=name,
                    level=level,
                    state=state,
                    url=url,
                    source_domain=parsed.hostname or "",
                    verified_on=VERIFIED_ON,
                    sort_order=sort_order,
                )
            )
        db.commit()
