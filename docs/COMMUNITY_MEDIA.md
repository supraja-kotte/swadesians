# Community photo diary and local media

The community page now has an Instagram-style **Profile** tab beside the
original **Questions** tab. The profile shows a three-column photo grid, a
profile header with a browser-local display name, and a lightbox viewer. Posts
can carry one photo or video; text-only questions keep working unchanged.

## What is stored

- Photos and videos are written to `backend/uploads/<year>/<month>/<uuid>.<ext>`
  and served from the same origin at `/uploads/...`.
- The database stores only a separate `community_media` row with the post ID,
  same-origin path, kind (`image`/`video`) and a sanitised original filename.
  A separate table means existing databases need no column migration.
- Nothing is uploaded to a CDN or a third-party service, and `backend/uploads/`
  is excluded from git and Docker builds. Mount a persistent volume there in
  production; otherwise uploaded files disappear when a container restarts.

The display name is kept in the browser's `localStorage` under
`agriguide.farmerName`. There is still no farmer login; the name is a label,
not an authenticated identity.

## Upload rules

| Rule | Value |
|---|---|
| Images | JPEG, PNG, WebP, GIF — max 8 MB |
| Videos | MP4, WebM — max 60 MB |
| Validation | Extension, declared content type and magic bytes must agree |
| Filename | The client never chooses the stored name; only a UUID is used |
| Rate limit | 10 uploads per client per 60 seconds, in process |

`POST /api/community/upload` accepts multipart form data and returns
`{path, kind, name, size}`. The client must map those to `media_path`,
`media_kind` and `media_name` when calling `POST /api/community/posts`. A post
rejects a media reference that does not resolve to a real file inside the
upload folder (`422`), so arbitrary paths cannot be stored.

The Content Security Policy allows same-origin and `blob:` images/media so the
local preview works. `blob:` URLs are revoked when the selection changes or a
post is published.

## Moderation and privacy

- Hiding a post removes it from the profile grid and question list; its media
  file is **not deleted**. A future cleanup job can remove unreferenced files.
- The admin queues include the media reference so a moderator can see what was
  reported.
- The UI tells farmers not to upload private information. There is no
  end-to-end encryption and no automated content scanning.

## Tests

`tests/test_community_media.py` covers image/video uploads, type and size
rejection, magic-byte validation, rate limiting, reference validation and
serialisation in list/detail views. Tests use a temporary upload folder through
the `UPLOAD_DIR` environment variable and never touch `backend/uploads/`.
