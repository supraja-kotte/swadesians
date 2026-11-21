# AgriGuide live release checklist

Version: **1.1.0-live**. This is the live working copy with real weather and
mandi data, farmer/admin accounts, no standalone Videos feature and no demo
content. Natural-language AI remains optional until a server-side key is set.

## Before sharing

1. From `backend`, run:

   ```powershell
   .\.venv\Scripts\python.exe -m scripts.release_check
   ```

   This runs all tests and scans runtime code for accidental API keys and the
   removed Crop Doctor feature. It must print **Release check passed.**

2. Start the server and open `http://127.0.0.1:8000/api/health`. It should
   return `status: ok` and version `1.1.0-live`. `/health` is also available for
   hosting-platform probes.

3. Check the five language buttons and the bottom navigation in a browser.

4. Create an administrator if moderation access is needed:

   ```powershell
   .\.venv\Scripts\python.exe -m scripts.create_admin
   ```

   There is no default password. Deleting `agri_guide.db` removes all admins.

5. Confirm that the browser console has no unexpected errors. A deliberate
   unauthenticated request will log its expected `401`, so distinguish test
   probes from app errors.

## What is hardened

- Security headers on every response: `nosniff`, `DENY` framing, referrer and
  permissions policies, and a restrictive Content Security Policy.
- CORS allows only the configured local origins and the HTTP methods/headers
  the app actually uses.
- Farmer and administrator sign-in are rate limited after five failed attempts
  per username and client for 15 minutes.
- Passwords are salted PBKDF2 hashes; sessions are random and expire after
  eight hours.
- Farmer and administrator sessions use separate HttpOnly cookies and separate
  double-submit CSRF tokens.
- `/api/health` and `/health` both report version and mode.

## Deployment notes

- Set `AGRIGUIDE_MODE=production` and a restrictive `ALLOWED_ORIGINS` list in
  `backend/.env` before any public deployment.
- Keep `backend/.env` out of source control. No API key belongs in `frontend/`.
- Use `DATABASE_URL` to switch from SQLite to PostgreSQL later.
- Run behind HTTPS so the `Secure` session cookies are sent by the browser.
  Cookies are already HttpOnly and `SameSite=Strict`, with CSRF protection on
  cookie-authenticated writes.
- The login rate limit is in-process only. Multiple workers need a shared store.

## Known limitations

- There is no password reset or email verification yet.
- One admin level only — no viewer/editor roles, audit log or account lockout
  beyond the short rate-limit window.
- Weather comes live from Open-Meteo and needs no API key. Mandi prices come
  live from Agmarknet/data.gov.in; no prices are invented when the feed fails.
- Equipment listings are entered by owners themselves; no owner, price, contact
  or availability is seeded. AgriGuide does not verify ownership or condition.
  See `docs/EQUIPMENT_RENTAL.md`.
- Marketplace shows only official live wholesale prices. Smart Farming contains
  five verified YouTube videos, and there is no standalone Videos page. Scheme
  data is generic official-source guidance with verified official links.
- Voice commands use the browser's own recognition and read-aloud. Natural
  answers require a server-side `AI_API_KEY`; without it the UI honestly shows
  fixed commands only.
- Translations have not had native-speaker review.

## Rollback

Git history on `main` is the primary rollback record; zip snapshots in
`_checkpoints/` remain as extra local backups. Use `git log` and
`git revert` on this machine, or restore a checkpoint zip as a last resort.
