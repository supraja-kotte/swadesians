import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";
import {
  farmerKey,
  farmerName,
  farmerPhone,
  ownerKey,
  saveFarmerContact,
} from "../services/localIdentity.js";

const equipmentState = {
  tab: "browse",
  view: "list",
  loading: false,
  listings: [],
  ownerListings: [],
  ownerEnquiries: [],
  farmerEnquiries: [],
  selected: null,
  category: "all",
  location: "",
  message: "",
  error: "",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function t(language, key) {
  return translate(language, key);
}

function categoryLabel(language, value) {
  const match = mockData.equipmentCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function badge(text, className = "") {
  return `<span class="community-badge ${className}">${escapeHtml(text)}</span>`;
}

function priceText(language, item) {
  if (!item.price_amount) return "—";
  const unitKey =
    item.price_unit === "hour"
      ? "pricePerHour"
      : item.price_unit === "season"
        ? "pricePerSeason"
        : "pricePerDay";
  return `₹${item.price_amount} ${t(language, unitKey)}`;
}

function listingStatusKey(status) {
  if (status === "paused") return "statusPaused";
  if (status === "hidden") return "statusHidden";
  return "statusActive";
}

function enquiryStatusKey(status) {
  if (status === "contacted") return "statusContacted";
  if (status === "closed") return "statusClosed";
  return "statusNew";
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

function jsonPost(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function jsonPatch(path, body, headers = {}) {
  return api(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
}

function renderTabs(language) {
  const tabs = [
    ["browse", "tabBrowse"],
    ["owner", "tabOwner"],
    ["farmer", "tabFarmer"],
  ];

  return `
    <div class="community-chips equipment-tabs">
      ${tabs
        .map(
          ([value, key]) =>
            `<button type="button" class="chip${equipmentState.tab === value ? " is-selected" : ""}"
              data-eq-tab="${value}">${t(language, key)}</button>`,
        )
        .join("")}
    </div>
  `;
}

function renderFilters(language) {
  const chips = [
    `<button type="button" class="chip${equipmentState.category === "all" ? " is-selected" : ""}" data-eq-category="all">${t(language, "allEquipment")}</button>`,
    ...mockData.equipmentCategories.map(
      (item) =>
        `<button type="button" class="chip${equipmentState.category === item.value ? " is-selected" : ""}" data-eq-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  const districts = mockData.equipmentDistricts
    .map(
      (name) =>
        `<button type="button" class="chip district-chip${equipmentState.location === name ? " is-selected" : ""}" data-district="${escapeHtml(name)}">${escapeHtml(name)}</button>`,
    )
    .join("");

  return `
    <div class="equipment-filters">
      <div class="community-chips">${chips}</div>
      <form id="equipment-location-form" class="search-row">
        <label class="visually-hidden" for="equipment-location">${t(language, "locationLabel")}</label>
        <input id="equipment-location" type="search" maxlength="60"
          placeholder="${t(language, "locationPlaceholder")}" value="${escapeHtml(equipmentState.location)}" />
        <button type="submit" class="primary-button">${t(language, "searchButton")}</button>
      </form>
      <div class="quick-places">${districts}</div>
      <button type="button" id="clear-equipment-filters" class="secondary-button">${t(language, "clearFilters")}</button>
    </div>
  `;
}

function renderPublicCard(language, item) {
  return `
    <article class="equipment-card">
      <div class="community-badges">
        ${badge(t(language, "ownerSubmitted"), "category")}
        ${badge(categoryLabel(language, item.category), "category")}
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.description)}</p>
      <p class="equipment-place">${icon("mapPin")} ${escapeHtml(item.district)}, ${escapeHtml(item.state)}</p>
      <p class="equipment-availability">${t(language, "availabilityLabel")}: ${escapeHtml(item.availability || "—")}</p>
      <p class="equipment-price">${escapeHtml(priceText(language, item))}</p>
      <p class="equipment-place">${t(language, "ownerLabel")}: ${escapeHtml(item.owner_label)}</p>
      <button type="button" class="primary-button" data-enquire="${escapeHtml(item.id)}">${t(language, "enquire")}</button>
    </article>
  `;
}

function renderEnquiryForm(language) {
  const item = equipmentState.selected;
  if (!item) return "";

  return `
    <div class="equipment-enquiry">
      <button type="button" id="equipment-back" class="secondary-button">${t(language, "backToListings")}</button>
      <article class="equipment-card is-selected">
        <div class="community-badges">${badge(categoryLabel(language, item.category), "category")}</div>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="equipment-place">${icon("mapPin")} ${escapeHtml(item.district)}, ${escapeHtml(item.state)}</p>
        <p class="equipment-price">${escapeHtml(priceText(language, item))}</p>
      </article>
      <section class="composer-card">
        <h3>${t(language, "enquiryHeading")}</h3>
        <p class="equipment-note">${t(language, "enquiryNote")}</p>
        <p class="equipment-note">${t(language, "contactPrivate")}</p>
        <form id="equipment-enquiry-form" class="profile-form">
          <label class="field-label" for="equipment-name">${t(language, "eqName")}</label>
          <input id="equipment-name" class="field-input" type="text" minlength="2" maxlength="60"
            value="${escapeHtml(farmerName())}" required />
          <label class="field-label" for="equipment-phone">${t(language, "fieldPhone")}</label>
          <input id="equipment-phone" class="field-input" type="tel" minlength="7" maxlength="20"
            placeholder="${t(language, "phonePlaceholder")}" value="${escapeHtml(farmerPhone())}" required />
          <label class="field-label" for="equipment-message">${t(language, "fieldMessage")}</label>
          <textarea id="equipment-message" class="field-input" rows="3" maxlength="500"
            placeholder="${t(language, "messagePlaceholder")}"></textarea>
          <div class="form-actions">
            <button type="submit" class="primary-button">${icon("check")} ${t(language, "sendEnquiry")}</button>
            <button type="button" id="equipment-cancel" class="secondary-button">${t(language, "cancel")}</button>
          </div>
        </form>
      </section>
    </div>
  `;
}

function renderBrowse(language) {
  if (equipmentState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  if (equipmentState.view === "enquiry") return renderEnquiryForm(language);

  const cards = equipmentState.listings.length
    ? equipmentState.listings.map((item) => renderPublicCard(language, item)).join("")
    : `<p class="weather-status">${t(language, "noListings")}</p>`;

  return `
    ${renderFilters(language)}
    <div class="equipment-grid">${cards}</div>
  `;
}

function renderAddListing(language) {
  const categories = mockData.equipmentCategories
    .map((item) => `<option value="${item.value}">${t(language, item.key)}</option>`)
    .join("");

  return `
    <div class="equipment-enquiry">
      <button type="button" id="equipment-back" class="secondary-button">${t(language, "backToListings")}</button>
      <section class="composer-card">
        <h3>${t(language, "addListingHeading")}</h3>
        <p class="equipment-note">${t(language, "identityNote")}</p>
        <form id="equipment-listing-form" class="profile-form">
          <label class="field-label" for="eq-title">${t(language, "eqTitleLabel")}</label>
          <input id="eq-title" class="field-input" type="text" minlength="4" maxlength="120"
            placeholder="${t(language, "eqTitlePlaceholder")}" required />

          <label class="field-label" for="eq-category">${t(language, "categoryLabel")}</label>
          <select id="eq-category" class="field-input" required>${categories}</select>

          <label class="field-label" for="eq-description">${t(language, "descriptionLabel")}</label>
          <textarea id="eq-description" class="field-input" rows="3" maxlength="800"
            placeholder="${t(language, "descriptionPlaceholder")}"></textarea>

          <div class="form-grid">
            <div>
              <label class="field-label" for="eq-state">${t(language, "stateLabel")}</label>
              <input id="eq-state" class="field-input" type="text" minlength="2" maxlength="60"
                placeholder="${t(language, "statePlaceholder")}" required />
            </div>
            <div>
              <label class="field-label" for="eq-district">${t(language, "districtLabel")}</label>
              <input id="eq-district" class="field-input" type="text" minlength="2" maxlength="60"
                placeholder="${t(language, "districtPlaceholder")}" required />
            </div>
          </div>

          <div class="form-grid">
            <div>
              <label class="field-label" for="eq-price">${t(language, "priceLabel")}</label>
              <input id="eq-price" class="field-input" type="number" min="1" max="10000000"
                placeholder="${t(language, "pricePlaceholder")}" required />
            </div>
            <div>
              <label class="field-label" for="eq-unit">${t(language, "priceUnitLabel")}</label>
              <select id="eq-unit" class="field-input">
                <option value="day">${t(language, "pricePerDay")}</option>
                <option value="hour">${t(language, "pricePerHour")}</option>
                <option value="season">${t(language, "pricePerSeason")}</option>
              </select>
            </div>
          </div>

          <label class="field-label" for="eq-owner-name">${t(language, "ownerNameLabel")}</label>
          <input id="eq-owner-name" class="field-input" type="text" minlength="2" maxlength="60"
            placeholder="${t(language, "ownerNamePlaceholder")}" value="${escapeHtml(farmerName())}" required />

          <label class="field-label" for="eq-contact">${t(language, "contactLabel")}</label>
          <input id="eq-contact" class="field-input" type="text" minlength="5" maxlength="120"
            placeholder="${t(language, "contactPlaceholder")}" value="${escapeHtml(farmerPhone())}" required />

          <label class="field-label" for="eq-availability">${t(language, "availabilityLabel")}</label>
          <input id="eq-availability" class="field-input" type="text" maxlength="120"
            placeholder="${t(language, "availabilityPlaceholder")}" />

          <div class="form-actions">
            <button type="submit" class="primary-button">${icon("check")} ${t(language, "publishListing")}</button>
            <button type="button" id="equipment-cancel" class="secondary-button">${t(language, "cancel")}</button>
          </div>
        </form>
      </section>
    </div>
  `;
}

function renderOwnerListing(language, item) {
  const isPaused = item.status === "paused";
  return `
    <article class="equipment-card">
      <div class="community-badges">
        ${badge(categoryLabel(language, item.category), "category")}
        ${badge(t(language, listingStatusKey(item.status)), "demo")}
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p class="equipment-place">${icon("mapPin")} ${escapeHtml(item.district)}, ${escapeHtml(item.state)}</p>
      <p class="equipment-price">${escapeHtml(priceText(language, item))}</p>
      <p class="equipment-place">${t(language, "ownerContactLabel")}: ${escapeHtml(item.owner_contact)}</p>
      <p class="report-note">${t(language, "newEnquiries")}: ${item.new_enquiries}</p>
      <button type="button" class="secondary-button" data-eq-status="${isPaused ? "active" : "paused"}"
        data-eq-listing="${escapeHtml(item.id)}">
        ${t(language, isPaused ? "resumeListing" : "pauseListing")}
      </button>
    </article>
  `;
}

function renderOwnerEnquiry(language, item) {
  const statuses = ["new", "contacted", "closed"];
  return `
    <article class="equipment-card enquiry-card" data-enquiry-card="${escapeHtml(item.id)}">
      <div class="community-badges">
        ${badge(t(language, enquiryStatusKey(item.status)), "category")}
      </div>
      <h3>${escapeHtml(item.listing_title)}</h3>
      <p class="report-note">${t(language, "farmerNameLabel")}: ${escapeHtml(item.farmer_name)} · ${escapeHtml(item.farmer_phone)}</p>
      <p>${escapeHtml(item.message)}</p>
      <label class="field-label" for="eq-status-${escapeHtml(item.id)}">${t(language, "enquiryStatusLabel")}</label>
      <select id="eq-status-${escapeHtml(item.id)}" class="field-input">
        ${statuses
          .map(
            (status) =>
              `<option value="${status}"${item.status === status ? " selected" : ""}>${t(language, enquiryStatusKey(status))}</option>`,
          )
          .join("")}
      </select>
      <label class="field-label" for="eq-reply-${escapeHtml(item.id)}">${t(language, "replyLabel")}</label>
      <textarea id="eq-reply-${escapeHtml(item.id)}" class="field-input" rows="2" maxlength="300"
        placeholder="${t(language, "replyPlaceholder")}">${escapeHtml(item.owner_reply)}</textarea>
      <button type="button" class="primary-button" data-eq-save="${escapeHtml(item.id)}">${t(language, "saveResponse")}</button>
    </article>
  `;
}

function renderOwner(language) {
  if (equipmentState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  if (equipmentState.view === "add") return renderAddListing(language);

  const listingCards = equipmentState.ownerListings.length
    ? equipmentState.ownerListings.map((item) => renderOwnerListing(language, item)).join("")
    : `<p class="weather-status">${t(language, "noOwnerListings")}</p>`;

  const enquiryCards = equipmentState.ownerEnquiries.length
    ? equipmentState.ownerEnquiries.map((item) => renderOwnerEnquiry(language, item)).join("")
    : `<p class="weather-status">${t(language, "noOwnerEnquiries")}</p>`;

  return `
    <p class="equipment-note smart-disclaimer">${t(language, "ownerIntro")}</p>
    <p class="equipment-note">${t(language, "identityNote")}</p>
    <button type="button" id="eq-add-listing" class="primary-button">${t(language, "addListingHeading")}</button>
    <section class="smart-section">
      <h3 class="smart-heading">${t(language, "myListingsHeading")}</h3>
      <div class="equipment-grid">${listingCards}</div>
    </section>
    <section class="smart-section">
      <h3 class="smart-heading">${t(language, "ownerEnquiriesHeading")}</h3>
      <div class="equipment-grid">${enquiryCards}</div>
    </section>
  `;
}

function renderFarmerEnquiry(language, item) {
  return `
    <article class="equipment-card enquiry-card">
      <div class="community-badges">
        ${badge(t(language, enquiryStatusKey(item.status)), "category")}
      </div>
      <h3>${escapeHtml(item.listing_title)}</h3>
      <p class="equipment-place">${t(language, "ownerLabel")}: ${escapeHtml(item.owner_label)}</p>
      <p class="report-note">${t(language, "ownerContactLabel")}: ${escapeHtml(item.owner_contact)}</p>
      <p class="report-note">${t(language, "ownerReplyLabel")}: ${escapeHtml(item.owner_reply || t(language, "noReplyYet"))}</p>
    </article>
  `;
}

function renderFarmer(language) {
  if (equipmentState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;

  const cards = equipmentState.farmerEnquiries.length
    ? equipmentState.farmerEnquiries.map((item) => renderFarmerEnquiry(language, item)).join("")
    : `<p class="weather-status">${t(language, "noFarmerEnquiries")}</p>`;

  return `
    <p class="equipment-note smart-disclaimer">${t(language, "farmerIntro")}</p>
    <p class="equipment-note">${t(language, "identityNote")}</p>
    <h3 class="smart-heading">${t(language, "myEnquiriesHeading")}</h3>
    <div class="equipment-grid">${cards}</div>
    <button type="button" id="eq-find-more" class="secondary-button">${t(language, "enquireAgain")}</button>
  `;
}

function renderView(language) {
  if (equipmentState.tab === "owner") return renderOwner(language);
  if (equipmentState.tab === "farmer") return renderFarmer(language);
  return renderBrowse(language);
}

function updateView(language) {
  const target = document.querySelector("#equipment-view");
  if (target) target.innerHTML = renderView(language);

  const tabs = document.querySelector("#equipment-tabs");
  if (tabs) tabs.innerHTML = renderTabs(language);

  const status = document.querySelector("#equipment-status");
  if (status) {
    status.textContent = equipmentState.message || equipmentState.error;
    status.className = equipmentState.error ? "error-message" : "success-message";
  }
}

function clearStatus() {
  equipmentState.message = "";
  equipmentState.error = "";
}

async function loadListings(language) {
  const params = new URLSearchParams();
  if (equipmentState.category !== "all") params.set("category", equipmentState.category);
  if (equipmentState.location.trim()) params.set("location", equipmentState.location.trim());

  const data = await api(`/api/equipment/listings?${params.toString()}`);
  equipmentState.listings = data.listings ?? [];
}

async function loadOwnerData() {
  const headers = { "X-Owner-Key": ownerKey() };
  const [listings, enquiries] = await Promise.all([
    api("/api/equipment/owner/listings", { headers }),
    api("/api/equipment/owner/enquiries", { headers }),
  ]);
  equipmentState.ownerListings = listings.listings ?? [];
  equipmentState.ownerEnquiries = enquiries.enquiries ?? [];
}

async function loadFarmerData() {
  const data = await api("/api/equipment/farmer/enquiries", {
    headers: { "X-Farmer-Key": farmerKey() },
  });
  equipmentState.farmerEnquiries = data.enquiries ?? [];
}

async function loadTab(language) {
  clearStatus();
  equipmentState.loading = true;
  equipmentState.view = "list";
  updateView(language);

  try {
    if (equipmentState.tab === "owner") await loadOwnerData();
    else if (equipmentState.tab === "farmer") await loadFarmerData();
    else await loadListings(language);
  } catch {
    equipmentState.error =
      equipmentState.tab === "owner"
        ? t(language, "listingLoadError")
        : equipmentState.tab === "farmer"
          ? t(language, "enquiryLoadError")
          : t(language, "loadError");
  } finally {
    equipmentState.loading = false;
    updateView(language);
  }
}

function openEnquiry(listingId, language) {
  equipmentState.selected = equipmentState.listings.find((item) => item.id === listingId) ?? null;
  if (!equipmentState.selected) return;
  equipmentState.view = "enquiry";
  clearStatus();
  updateView(language);
}

async function submitEnquiry(language) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const name = value("#equipment-name");
  const phone = value("#equipment-phone");

  try {
    await jsonPost(
      `/api/equipment/listings/${encodeURIComponent(equipmentState.selected.id)}/enquiries`,
      {
        name,
        phone,
        message: value("#equipment-message"),
        farmer_key: farmerKey(),
      },
    );
    saveFarmerContact(name, phone);
    equipmentState.view = "list";
    equipmentState.selected = null;
    equipmentState.message = t(language, "enquirySent");
    equipmentState.error = "";
    await loadListings(language);
  } catch {
    equipmentState.error = t(language, "createError");
  }
  updateView(language);
}

async function submitListing(language) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const payload = {
    category: value("#eq-category"),
    title: value("#eq-title"),
    description: value("#eq-description"),
    state: value("#eq-state"),
    district: value("#eq-district"),
    price_amount: Number(value("#eq-price")),
    price_unit: value("#eq-unit"),
    owner_label: value("#eq-owner-name"),
    owner_contact: value("#eq-contact"),
    availability: value("#eq-availability"),
    owner_key: ownerKey(),
  };

  try {
    await jsonPost("/api/equipment/listings", payload);
    saveFarmerContact(payload.owner_label, payload.owner_contact);
    equipmentState.view = "list";
    equipmentState.message = t(language, "listingPublished");
    equipmentState.error = "";
    await loadOwnerData();
  } catch {
    equipmentState.error = t(language, "createError");
  }
  updateView(language);
}

async function setListingStatus(language, listingId, status) {
  try {
    await jsonPatch(
      `/api/equipment/owner/listings/${encodeURIComponent(listingId)}`,
      { status },
      { "X-Owner-Key": ownerKey() },
    );
    equipmentState.message = t(language, "listingUpdated");
    equipmentState.error = "";
    await loadOwnerData();
  } catch {
    equipmentState.error = t(language, "listingLoadError");
  }
  updateView(language);
}

async function saveEnquiryResponse(language, enquiryId, card) {
  try {
    await jsonPatch(
      `/api/equipment/owner/enquiries/${encodeURIComponent(enquiryId)}`,
      {
        status: card.querySelector("select")?.value ?? "new",
        reply: card.querySelector("textarea")?.value ?? "",
      },
      { "X-Owner-Key": ownerKey() },
    );
    equipmentState.message = t(language, "responseSaved");
    equipmentState.error = "";
    await loadOwnerData();
  } catch {
    equipmentState.error = t(language, "enquiryLoadError");
  }
  updateView(language);
}

function attachEvents(language) {
  const root = document.querySelector("#equipment-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-eq-tab]");
    if (tab) {
      equipmentState.tab = tab.dataset.eqTab;
      loadTab(language);
      return;
    }

    const category = event.target.closest("[data-eq-category]");
    if (category) {
      equipmentState.category = category.dataset.eqCategory;
      equipmentState.view = "list";
      loadListings(language).then(() => updateView(language)).catch(() => {
        equipmentState.error = t(language, "loadError");
        updateView(language);
      });
      return;
    }

    const district = event.target.closest("[data-district]");
    if (district) {
      equipmentState.location = district.dataset.district;
      equipmentState.view = "list";
      loadListings(language).then(() => updateView(language)).catch(() => {
        equipmentState.error = t(language, "loadError");
        updateView(language);
      });
      return;
    }

    if (event.target.closest("#clear-equipment-filters")) {
      equipmentState.category = "all";
      equipmentState.location = "";
      equipmentState.view = "list";
      loadListings(language).then(() => updateView(language)).catch(() => {
        equipmentState.error = t(language, "loadError");
        updateView(language);
      });
      return;
    }

    const enquire = event.target.closest("[data-enquire]");
    if (enquire) {
      openEnquiry(enquire.dataset.enquire, language);
      return;
    }

    if (event.target.closest("#eq-add-listing")) {
      equipmentState.view = "add";
      clearStatus();
      updateView(language);
      return;
    }

    if (event.target.closest("#eq-find-more")) {
      equipmentState.tab = "browse";
      loadTab(language);
      return;
    }

    const statusButton = event.target.closest("[data-eq-status]");
    if (statusButton) {
      setListingStatus(language, statusButton.dataset.eqListing, statusButton.dataset.eqStatus);
      return;
    }

    const saveButton = event.target.closest("[data-eq-save]");
    if (saveButton) {
      const card = saveButton.closest("[data-enquiry-card]");
      if (card) saveEnquiryResponse(language, saveButton.dataset.eqSave, card);
      return;
    }

    if (event.target.closest("#equipment-back") || event.target.closest("#equipment-cancel")) {
      equipmentState.view = "list";
      equipmentState.selected = null;
      clearStatus();
      updateView(language);
    }
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id === "equipment-location-form") {
      event.preventDefault();
      equipmentState.location = document.querySelector("#equipment-location")?.value ?? "";
      equipmentState.view = "list";
      loadListings(language).then(() => updateView(language)).catch(() => {
        equipmentState.error = t(language, "loadError");
        updateView(language);
      });
    } else if (event.target.id === "equipment-enquiry-form") {
      event.preventDefault();
      submitEnquiry(language);
    } else if (event.target.id === "equipment-listing-form") {
      event.preventDefault();
      submitListing(language);
    }
  });
}

export function renderEquipment(language) {
  return `
    <section class="equipment-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-sky">${icon("tractor")}</div>
        <div>
          <h2>${t(language, "equipmentTitle")}</h2>
          <p>${t(language, "equipmentIntro")}</p>
        </div>
      </header>
      <p class="equipment-note smart-disclaimer">${t(language, "equipmentDisclaimer")}</p>
      <p id="equipment-status" class="success-message" role="status"></p>
      <div id="equipment-root">
        <div id="equipment-tabs">${renderTabs(language)}</div>
        <div id="equipment-view">${`<p class="weather-status">${t(language, "weatherLoading")}</p>`}</div>
      </div>
    </section>
  `;
}

export function initEquipment(language) {
  attachEvents(language);
  updateView(language);
  loadTab(language);
}
