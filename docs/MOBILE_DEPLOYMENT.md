# Mobile deployment (PWA)

AgriGuide is a responsive web app that is also an **installable PWA**. Farmers
and judges open one HTTPS link, then choose **Add to Home screen** / **Install
app** to get an icon that opens full-screen like a mobile app. There is no app
store and no separate iOS/Android codebase.

## What was added

- `frontend/manifest.webmanifest` — app name, theme colour, icons and shortcuts
- `frontend/sw.js` — caches only the static app shell; live API data stays online
- `frontend/icons/` — 192 px, 512 px and Apple touch icons
- `frontend/index.html` — manifest, theme colour and mobile meta tags
- `frontend/src/app.js` — service-worker registration
- `render.yaml` — one-click deployment of the FastAPI app + free Postgres

## Deploy on Render (free)

The source is already on GitHub at `https://github.com/supraja-kotte/swadesians`.

1. Create a free account at <https://dashboard.render.com/register>.
2. Click **New → Blueprint**.
3. Connect the GitHub repository `supraja-kotte/swadesians`.
4. Select branch `main` and confirm the blueprint name.
5. Click **Apply**. Render creates:
   - `agriguide` — Python web service (`Free` plan, Singapore region)
   - `agriguide-db` — managed Postgres (`Free` plan)
6. Wait until the service shows **Live**. First deploy usually takes a few minutes.
7. Open the service URL, for example `https://agriguide.onrender.com`.
8. Check `https://<your-service>.onrender.com/health`; it should return
   `{"status":"ok","service":"AgriGuide","version":"1.1.0-live"}`.

The blueprint sets `DATABASE_URL` from the managed Postgres database, so real
registrations, profiles, community data and equipment data survive redeploys.

## Install on a phone

### Android (Chrome)

1. Open the deployed HTTPS URL.
2. Tap the three-dot menu.
3. Tap **Install app** or **Add to Home screen**.
4. Confirm. AgriGuide now opens full-screen from the home screen.

### iPhone (Safari)

1. Open the deployed HTTPS URL in Safari.
2. Tap the **Share** button.
3. Tap **Add to Home Screen**.
4. Confirm. AgriGuide now opens from the home screen.

## Verify the installable app

- `GET /health` → `200` with version `1.1.0-live`
- `GET /manifest.webmanifest` → `200` with `display: "standalone"`
- `GET /sw.js` → `200`
- Home screen shows the **NASA field advisor** card
- NASA page loads live data; Weather and Marketplace load live data
- Browser console has no unexpected errors

## Important free-tier limits

- A free web service sleeps after about 15 minutes with no traffic. The next
  open may show a loading page for about a minute while it wakes up.
- A free Postgres database expires 30 days after creation. Before judging or a
  farmer rollout, either upgrade it or create a fresh one close to the event.
- Uploaded community photos/videos are written to `/tmp/agriguide-uploads` on
  the free plan and disappear when the service restarts. For permanent media,
  attach a paid persistent disk or use object storage.
- Weather, mandi and NASA data need internet. The service worker only caches
  the app shell; it does not fake offline live data.
- There is no default administrator. Create one after deployment with
  `python -m scripts.create_admin` if moderation is needed.

## Optional production settings

Set these in the Render service environment if needed:

| Variable | Purpose |
|---|---|
| `ALLOWED_ORIGINS` | Comma-separated HTTPS origins allowed to call the API |
| `DATA_GOV_API_KEY` | Your own Agmarknet/data.gov.in key |
| `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL` | Server-side AI answers; never put these in the frontend |
| `AGRIGUIDE_MODE` | Keep `production` for Secure cookies and HTTPS behaviour |

If you use a custom domain, update `ALLOWED_ORIGINS` to include it and redeploy.
