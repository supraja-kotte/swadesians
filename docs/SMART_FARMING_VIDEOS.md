# Smart Farming videos

The Smart Farming page replaced its field-note form with **five real YouTube
videos**. No video title, benefit, price, price claim or advice was invented.
Only neutral IDs, categories and public watch URLs are stored in the database;
every farmer-facing word is in `frontend/src/i18n/smartFarmingStrings.js`.

## Verification

Each URL below was checked through YouTube's public oEmbed endpoint on
**2026-11-21**. The watch URL and publisher are reproduced exactly as returned.

| Internal ID | Category | Watch URL | Publisher |
|---|---|---|---|
| `soil-health-campaign` | soil | https://www.youtube.com/watch?v=9CKCQHISsLM | ICAR-Indian Institute of Soil Science, Bhopal |
| `green-manuring` | soil | https://www.youtube.com/watch?v=wWolzhA1yV4 | ICAR RC NEH_Podcast |
| `soil-health-card` | soil | https://www.youtube.com/watch?v=E0-Dua2eWNQ | ICAR RC NEH_Podcast |
| `integrated-pest-management` | pests | https://www.youtube.com/watch?v=b86Be4pw7HI | ICAR RC NEH_Podcast |
| `irrigation-water-management` | water | https://www.youtube.com/watch?v=GCFCReu2J2o | TheUSDANRCS |

## How they are shown

- `GET /api/smart-farming/videos` returns `{id, category, url, sort_order, is_demo}`.
- The frontend converts the watch URL to a `youtube-nocookie.com/embed/<id>`
  player. Only `youtube.com`, `www.youtube.com` and `m.youtube.com` hosts are
  accepted, and the video ID must be 11 URL-safe characters.
- The Content Security Policy allows frames from `youtube-nocookie.com` and
  `youtube.com` only.
- A direct “Watch on YouTube” link is always shown beside the player. If a
  publisher disables embedding or the video is removed, that link still works.
- The spoken language of a video is the publisher's choice. It does not change
  with the AgriGuide language picker; the page says this plainly.

## Not included

- No YouTube Data API key is used, so no search results, view counts or
  recommendations are fetched.
- No video is claimed to be translated by AgriGuide.
- No equipment, mandi or marketplace video is presented as real data.

Re-run the oEmbed checks before changing this list, and record the new date
here.
