# Verified government scheme sources

**Verification date: 2026-11-21.** The directory lives in
`backend/app/db/seed_scheme_links.py` and is served by `GET /api/schemes/links`.

## Policy

- Only official Indian government domains (`gov.in`, `nic.in` and state
  government subdomains) are accepted. `is_official_url()` enforces HTTPS and
  an exact-domain or subdomain match, so a look-alike host is rejected.
- Scheme names are proper nouns. The app stores **no benefit amounts,
  eligibility rules, application promises, translated scheme facts or
  "apply now" claims**.
- Each link is a pointer to the authoritative page. Current rules, status and
  availability must be checked there. A listed link does not mean a scheme is
  open or that a farmer is eligible.
- Two AP district pages and one Telangana state initiative page are grouped as
  **state information pages**, not application portals, because their status
  can change with the agricultural season.
- Re-run the verification before every release:

  ```powershell
  .\.venv\Scripts\python.exe -m scripts.verify_scheme_links
  .\.venv\Scripts\python.exe -m scripts.verify_scheme_links --strict
  ```

  `--strict` also performs HTTP requests. Some government sites block
  automated clients, so a network warning is not by itself a removal reason;
  record the result and re-check manually in a browser.

## Central government (9)

| Scheme / page | Official URL |
|---|---|
| Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) | https://pmkisan.gov.in/ |
| Pradhan Mantri Fasal Bima Yojana (PMFBY) | https://pmfby.gov.in/ |
| e-National Agriculture Market (eNAM) | https://enam.gov.in/ |
| Soil Health Card | https://soilhealth.dac.gov.in/ |
| Agriculture Infrastructure Fund (AIF) | https://agriinfra.dac.gov.in/ |
| National Mission on Natural Farming (NMNF) | https://naturalfarming.dac.gov.in/Schemes |
| National Mission on Sustainable Agriculture (NMSA) | https://nmsa.dac.gov.in/ |
| PM-KISAN on the Digital India portal | https://www.digitalindia.gov.in/initiative/pm-kisan |
| PM-KISAN registration — National Portal of India | https://www.india.gov.in/services/details/register-as-a-new-farmer-for-pradhan-mantri-kisan-samman-nidhi-pm-kisan |

## Andhra Pradesh (2)

| Scheme / page | Official URL |
|---|---|
| Annadata Sukhibhava – PM KISAN | https://annadathasukhibhava.ap.gov.in/ |
| YSR Rythu Bharosa (district agriculture information) | https://spsnellore.ap.gov.in/agriculture |

## Telangana (2)

| Scheme / page | Official URL |
|---|---|
| Rythu Bharosa and Rythu Bima state farmer portal | https://www.rythubharosa.telangana.gov.in/Default_Home.aspx |
| Telangana Government Initiatives | https://www.telangana.gov.in/government-initiatives |

## Addition checklist

1. Confirm the URL is on an official government domain.
2. Open it and confirm the page title matches the scheme name.
3. Confirm no amount, eligibility or status claim is copied into the app.
4. Add the row to `VERIFIED_LINKS` with `level`, optional `state` and today's
   `verified_on` value.
5. Add the same row to this document and run the tests.
