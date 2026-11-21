# Equipment rental — user-submitted workflow

The old demo-only equipment page has been replaced. AgriGuide no longer seeds
sample renters, owners, prices or availability. A person who owns equipment
adds their own listing, and a farmer contacts that owner directly. Owners can
also publish a renter profile so farmers can find them by equipment type and
place even before a specific machine is listed.

## What is real in this workflow

- **Listings** are typed by the owner: title, description, category, state,
  district, rental rate, unit, owner label, contact detail and availability.
- **Renter profiles** are typed by the provider: display name, contact, state,
  district, equipment categories, availability and a short description. A
  public profile can be paused by its owner.
- **Contact details and rates** are entered by the owner and are never invented
  by the app. Public listing and renter cards deliberately hide contact
  details; they appear only after a farmer sends an enquiry.
- **Enquiries** are written by the farmer and stored in the database. They
  include the farmer's name, phone, optional message and status. A farmer can
  enquire about a listing or contact a renter profile directly.
- **Replies** are written by the owner and are visible to the farmer who sent
  the enquiry.
- **Moderation** is performed by an administrator: a listing can be hidden from
  public results and restored.

AgriGuide does **not** verify ownership, equipment condition, insurance, rates
or the identity of either party. The page says so in every language. Farmers
and owners must check these things themselves before paying or handing over
equipment.

## Privacy model (browser keys for rental)

Farmer accounts now exist on the sign-in page for farm profiles, but equipment
rental still uses browser keys so farmers can contact an owner or renter without
first creating an account. The browser generates a random private key and keeps
it in `localStorage`:

- `agriguide.equipmentOwnerKey` — return to your own listings and enquiries.
- `agriguide.equipmentFarmerKey` — return to enquiries you have sent.

Only a **SHA-256 hash** of each key is stored in the database. Raw keys are
never stored in a table and are never returned in an API response. Losing the
browser or clearing site data loses access to those private views; the public
listing and the owner's own contact detail remain in the database.

The farmer's name and phone are reused from the community display name where
available, but are always editable in the enquiry form.

## Pages

The Equipment page has four tabs:

1. **Browse equipment** — category chips, free-text district/state search,
   quick district picks and public cards. Contact detail appears only after an
   enquiry is sent.
2. **Find renters** — browse user-entered renter profiles with the same
   category and place filters, open a live detail view with the renter's current
   equipment, and send a direct enquiry.
3. **I have equipment** — create or edit a renter profile, add a listing, see
   listings with new-enquiry counts, pause/resume a listing, and reply to or
   close enquiries from both listings and the renter profile. Listing forms are
   pre-filled from the saved renter profile.
4. **My enquiries** — enquiries sent from this browser to listings and renter
   profiles, with the submitted contact detail and any reply.

Both public tabs reload from the API when the tab opens, when filters change,
and after a profile, listing, status or enquiry is saved. Opening a renter's
details fetches that profile and its equipment again from the server, so the
two tabs stay connected without a manual page refresh.

An administrator sees an **Equipment rental** section on the Admin page with
all owner-submitted listings and enquiries, and can hide or restore a listing.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/equipment/listings` | Public active listings, optional `category` and `location` filters |
| `POST` | `/api/equipment/listings` | Owner publishes a listing (`owner_key` in body) |
| `GET` | `/api/equipment/owner/listings` | Owner's listings (`X-Owner-Key` header) |
| `PATCH` | `/api/equipment/owner/listings/{id}` | Owner edits or pauses/resumes a listing |
| `GET` | `/api/equipment/owner/enquiries` | Enquiries for the owner's listings |
| `PATCH` | `/api/equipment/owner/enquiries/{id}` | Owner sets status and adds a reply |
| `GET` | `/api/equipment/farmer/enquiries` | Farmer's own enquiries (`X-Farmer-Key` header) |
| `POST` | `/api/equipment/listings/{id}/enquiries` | Farmer sends an enquiry |
| `GET` | `/api/equipment/providers` | Public active renter profiles, optional `category` and `location` filters |
| `GET` | `/api/equipment/providers/{id}` | One live public renter profile with its current equipment, contact hidden |
| `PUT` | `/api/equipment/owner/provider` | Owner creates or updates a renter profile (`X-Owner-Key` header) |
| `GET` | `/api/equipment/owner/provider` | Owner's renter profile, if one exists |
| `POST` | `/api/equipment/providers/{id}/enquiries` | Farmer sends a direct renter enquiry |
| `GET` | `/api/equipment/owner/provider/enquiries` | Enquiries sent to the owner's renter profile |
| `PATCH` | `/api/equipment/owner/provider/enquiries/{id}` | Owner sets status and adds a reply |
| `GET` | `/api/equipment/farmer/provider-enquiries` | Farmer's own renter enquiries, with contacts |
| `GET` | `/api/admin/equipment/listings` | Admin review queue (admin session/token) |
| `PATCH` | `/api/admin/equipment/listings/{id}` | Admin hides or restores a listing |
| `GET` | `/api/admin/equipment/enquiries` | Admin enquiry oversight |

`X-Owner-Key`, `X-Farmer-Key` and `X-CSRF-Token` are allowed CORS headers.

## Data and migration

`equipment_listings` gained `owner_contact`, `owner_key_hash`, `availability`
and `status`; `equipment_enquiries` gained `farmer_key_hash` and `owner_reply`.
`init_db()` calls `ensure_schema()`, which adds missing columns to an existing
SQLite database before any reference content is seeded. The renter tables
`equipment_providers` and `equipment_provider_enquiries` are created by
`Base.metadata.create_all()`. No sample listings or renters are inserted, and
old sample rows are excluded from every public and owner-facing view. A fresh
database starts with no equipment listings or renters.

Server-side text stays neutral: categories, units and statuses are IDs, and
all farmer-facing sentences live in the five i18n dictionaries.
