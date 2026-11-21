# AgriGuide demo release checklist

Version: **1.0.0-demo**. This is a complete, honestly labelled demo — not a
production deployment with real farmer accounts, verified scheme data or an AI
service.

## Before sharing

1. From `backend`, run:

   ```powershell
   .\.venv\Scripts\python.exe -m scripts.release_check
   ```

   This runs all tests and scans runtime code for accidental API keys and the
   removed Crop Doctor feature. It must print **Release check passed.**

2. Start the server and open `http://127.0.0.1:8000/api/health`. It should
   return `status: ok` and the demo version. `/health` is also available for
   hosting-platform probes.

3. Check the five language buttons and the bottom navigation in a browser.

4. Create an administrator only if moderation needs to be demonstrated:

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
- Administrator sign-in is rate limited after five failed attempts per
  username and client for 15 minutes.
- Passwords are salted PBKDF2 hashes; sessions are random and expire after
  eight hours.
- `/api/health` and `/health` both report version and mode.

## Deployment notes

- Set `AGRIGUIDE_MODE=production` and a restrictive `ALLOWED_ORIGINS` list in
  `backend/.env` before any public deployment.
- Keep `backend/.env` out of source control. No API key belongs in `frontend/`.
- Use `DATABASE_URL` to switch from SQLite to PostgreSQL later.
- Run behind HTTPS. The current Bearer token is stored in `localStorage`; a
  production service should move to HttpOnly, Secure, SameSite cookies.
- The login rate limit is in-process only. Multiple workers need a shared store.

## Known demo limitations

- No farmer accounts or password reset; posts use a random browser ID.
- One admin level only — no viewer/editor roles, audit log or account lockout
  beyond the short rate-limit window.
- Weather is the only live external data source, and it needs no API key.
- Equipment listings are entered by owners themselves; no owner, price, contact
  or availability is seeded. AgriGuide does not verify ownership or condition.
  See `docs/EQUIPMENT_RENTAL.md`.
- Marketplace and videos are clearly labelled samples, and scheme data is
  generic official-source guidance. No invented sellers, prices, videos, scheme
  names or benefit amounts are presented as real.
- Voice commands use the browser's own recognition and read-aloud. There is no
  AI model and no free-form answer endpoint.
- Translations have not had native-speaker review.

## Rollback

Git history on `main` is the primary rollback record; zip snapshots in
`_checkpoints/` remain as extra local backups. Use `git log` and
`git revert` on this machine, or restore a checkpoint zip as a last resort.
