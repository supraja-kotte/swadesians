# Hosting and GitHub notes

## Current machine status

Git is installed and this project is connected to
`https://github.com/supraja-kotte/swadesians.git` on `main`; the code
has been pushed. `gh`, `docker` and `psql` are still not installed here, so
repository administration and deployment are done through the GitHub website or
from another machine. A hosting platform and production secrets are still
needed before a public deploy.

## Repository files pushed

- `.github/workflows/ci.yml` — runs all pytest tests on push and pull request.
- `Dockerfile` — builds the FastAPI backend plus the static frontend.
- `.dockerignore` — keeps virtualenvs, databases, caches, secrets and community uploads out of builds.
- `scripts/migrate.py` — creates missing tables for the configured database.
- `backend/uploads/` — local community media. Mount a persistent volume at
  `/app/backend/uploads` when using the Dockerfile; otherwise uploaded photos
  and videos disappear on container restart.

## What GitHub alone cannot host

GitHub can store the code and run CI, but **GitHub Pages cannot run this
FastAPI backend**. A deployment platform is still needed. Connect the GitHub
repository to one of:

- **Render / Railway** — use the included Dockerfile, set `PORT=8000`, attach Postgres.
- **A VPS** — install Docker, run the image behind Nginx + HTTPS.
- **Another Python host** — set the start command to
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## Information still needed from you

1. The deployment platform and its service/database details.
2. The production `DATABASE_URL` (keep it secret; never paste it into frontend code).
3. A production domain, if any.

## Before the first public deploy

- Set `AGRIGUIDE_MODE=production` so auth cookies get `Secure`.
- Set `ALLOWED_ORIGINS` to the real public domain only.
- Set a strong `ADMIN_PASSWORD` through `scripts.create_admin`; there is no default.
- Put all keys in the platform's secret environment settings, not in files.
- Run `scripts.migrate.py` against the production database before starting the app.

## Local database migration

SQLite still works by default. To prepare PostgreSQL:

```powershell
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://user:password@host:5432/agriguide"
.\.venv\Scripts\python.exe -m scripts.migrate
```

`migrate.py` creates missing tables. It does not yet alter existing tables;
Alembic should be added before changing columns in live data.
