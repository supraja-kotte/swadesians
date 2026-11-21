# AgriGuide decision log

This file records the choices made before implementation began.

| Decision | Choice | Reason |
|---|---|---|
| Frontend | Plain HTML, CSS and JavaScript | Chosen by the user; beginner-friendly, no build step |
| Mock data path | `frontend/src/services/mockData.js` | Keeps the requested `src/services/` location; `.js` instead of `.ts` because the browser cannot load TypeScript directly |
| Backend | Python + FastAPI | Validated APIs and automatic documentation |
| Database | SQLite initially, PostgreSQL-ready | Simple local development now, upgrade path later |
| API keys | Available, stored in `backend/.env` | Keys must stay on the server, never in the browser |
| First language and region | Telugu, Andhra Pradesh and Telangana | Chosen by the user |
| Crop Doctor | Removed completely | Chosen by the user; no UI, data, API or phase includes it |
| Admin authentication | Salted PBKDF2 hashes and expiring random session tokens | No auth library was installed; this is a real salted hash using the Python standard library, not plain text |
| Default admin | None — created explicitly with `scripts.create_admin` | Avoids a known default password; a database reset removes all admins |
| Moderation access control | Admin token required for status changes and hidden-content reads | General reading and posting stay open; only privileged actions are protected |
| Release version | `1.0.0-demo` | Marks a complete demo without claiming production readiness |
| Security headers | `nosniff`, frame denial, referrer/permissions policies and CSP | Cheap, standard protection for a browser app; CSP allows self-hosted scripts, the existing Google Fonts and YouTube frames only |
| Login rate limiting | Five failures per username/client in 15 minutes | Simple in-process guard against password guessing; a multi-worker deployment needs a shared store |
| CORS | Configured local origins, `GET/POST/PATCH/OPTIONS`, `Authorization`/`Content-Type`/`X-CSRF-Token`/`X-Owner-Key`/`X-Farmer-Key` | Removes unnecessary wildcard permissions while allowing the cookie and private-key headers the app needs |
| Admin session transport | HttpOnly, Secure-in-production, SameSite=Strict cookie plus a readable double-submit CSRF token | JavaScript cannot steal the session token; writes still need a matching header. Bearer auth is kept for API clients |
| PostgreSQL driver | `psycopg[binary]`, plain `postgresql://` URLs normalised to `postgresql+psycopg://` | No DSN rewrite needed by the user; SQLAlchemy code stays identical |
| Migration step | `scripts/migrate.py` creates missing tables only | Safe for a fresh database; Alembic is required before altering live columns |
| Scheme sources | 13 verified official links, categorised central/AP/Telangana, stored with a verification date | Gives farmers authoritative URLs without inventing amounts, eligibility or application claims |
| Scheme link policy | HTTPS + `gov.in`/`nic.in` exact-domain/subdomain allowlist only | Prevents look-alike hosts from entering the directory |
| Translation review | Generated `docs/TRANSLATION_REVIEW.md`, all rows `PENDING` | No human approval is claimed; a native speaker must sign off per language |
| AI provider | OpenAI-compatible chat completions or Gemini, selected by `AI_PROVIDER` | One server-side key, standard library only; no frontend secret |
| AI answer style | Prose in the selected language, no IDs/codes/binary notation, no invented facts | Meets the "human language" requirement while keeping demo guardrails |
| Assistant free-form limit | 20 questions per client per 60 seconds, in-process | Protects the API key from casual abuse; shared store needed for many workers |
| Assistant speech | Device voices via `voiceLang()` with `en-IN`/`te-IN`/`hi-IN`/`ta-IN`/`mr-IN` | Human-sounding local speech without a second key; voice quality varies by device |
| Community media storage | New `community_media` table, UUID files in `backend/uploads/`, served at `/uploads` | Profile photos/videos need no column migration on existing databases and never leave this server |
| Community upload rules | JPEG/PNG/WebP/GIF ≤ 8 MB, MP4/WebM ≤ 60 MB; extension + MIME + magic bytes must agree | Blocks disguised files while keeping the local store simple; a CDN would need more policy work |
| Community identity | Display name in browser `localStorage`, not an account | Keeps posting open; the name is a label, not an authenticated identity |
| Smart farming media | Six guidance topics kept; field-note form replaced by five verified public YouTube embeds | Farmer asked for useful videos; no API key is needed for public embeds and no video claim is invented |
| Video data policy | Backend stores neutral IDs, categories and URLs; titles, publishers and notes stay in frontend i18n | Keeps translations in one place and prevents invented facts in the database |
| Video player | `youtube-nocookie.com/embed/<id>` with a direct YouTube link fallback | Reduces third-party cookies while keeping a working link if embedding is blocked |
| Equipment rental | Owners add their own listings; no seeded renters, sellers, prices or contacts | Replaces the demo-only list and enquiry notice with a real two-sided workflow |
| Equipment identity | Random per-browser private keys, stored only as SHA-256 hashes | Lets owners and farmers return to rental records without requiring a login for that workflow or storing raw keys |
| Equipment visibility | Public cards hide contact detail until an enquiry is sent; owners can pause, admins can hide | Gives owners control over their details and a moderation path without blocking honest enquiries |

## Rules we committed to

- General information is available without login.
- Personalisation is optional; signed-in farmers save their farm profile to their account.
- Farmer and administrator sessions are separate and use HttpOnly cookies with CSRF protection.
- No mock data, simulated sensors or demo answers are presented as real.
- Government scheme facts come from official, verified sources with a verification date.
- No fake sellers or fake products are presented as real.
- Each phase stays runnable and ends with a short report.
