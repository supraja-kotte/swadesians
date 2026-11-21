import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";

const equipmentState = {
  loading: true,
  listings: [],
  category: "all",
  location: "",
  selected: null,
  enquiryOpen: false,
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

function t(language, key, values = {}) {
  let text = translate(language, key);
  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

function categoryLabel(language, value) {
  const match = mockData.equipmentCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function badge(text, className = "") {
  return `<span class="community-badge ${className}">${escapeHtml(text)}</span>`;
}

function renderFilters(language) {
  const chips = [
    `<button type="button" class="chip${equipmentState.category === "all" ? " is-selected" : ""}" data-eq-category="all">${t(language, "allCategories")}</button>`,
    ...mockData.equipmentCategories.map(
      (item) =>
        `<button type="button" class="chip${equipmentState.category === item.value ? " is-selected" : ""}" data-eq-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  const districts = mockData.equipmentDistricts
    .map(
      (name) =>
        `<button type="button" class="chip district-chip" data-district="${escapeHtml(name)}">${escapeHtml(name)}</button>`,
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

function renderListingCard(language, item) {
  return `
    <article class="equipment-card">
      <div class="community-badges">
        ${badge(t(language, "demoListing"), "demo")}
        ${badge(categoryLabel(language, item.category), "category")}
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.description)}</p>
      <p class="equipment-place">${icon("mapPin")} ${escapeHtml(item.district)}, ${escapeHtml(item.state)}</p>
      <p class="equipment-price">${t(language, "priceUnavailable")}</p>
      <button type="button" class="primary-button" data-enquire="${escapeHtml(item.id)}">${t(language, "enquire")}</button>
    </article>
  `;
}

function renderList(language) {
  const cards = equipmentState.listings.length
    ? equipmentState.listings.map((item) => renderListingCard(language, item)).join("")
    : `<p class="weather-status">${t(language, "noListings")}</p>`;

  return `
    ${renderFilters(language)}
    <div class="equipment-grid">${cards}</div>
  `;
}

function renderEnquiry(language) {
  const item = equipmentState.selected;
  if (!item) return "";

  return `
    <div class="equipment-enquiry">
      <button type="button" id="equipment-back" class="secondary-button">${t(language, "backToListings")}</button>
      <article class="equipment-card is-selected">
        <div class="community-badges">
          ${badge(t(language, "demoListing"), "demo")}
          ${badge(categoryLabel(language, item.category), "category")}
        </div>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="equipment-place">${icon("mapPin")} ${escapeHtml(item.district)}, ${escapeHtml(item.state)}</p>
      </article>
      <section class="composer-card">
        <h3>${t(language, "enquiryHeading")}</h3>
        <p class="equipment-note">${t(language, "enquiryNote")}</p>
        <form id="equipment-enquiry-form" class="profile-form">
          <label class="field-label" for="equipment-name">${t(language, "eqName")}</label>
          <input id="equipment-name" class="field-input" type="text" minlength="2" maxlength="60" required />
          <label class="field-label" for="equipment-phone">${t(language, "fieldPhone")}</label>
          <input id="equipment-phone" class="field-input" type="tel" minlength="7" maxlength="20"
            placeholder="${t(language, "phonePlaceholder")}" required />
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

function renderView(language) {
  if (equipmentState.enquiryOpen) return renderEnquiry(language);
  if (equipmentState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  return renderList(language);
}

function updateView(language) {
  const target = document.querySelector("#equipment-view");
  if (target) target.innerHTML = renderView(language);

  const status = document.querySelector("#equipment-status");
  if (status) {
    status.textContent = equipmentState.message || equipmentState.error;
    status.className = equipmentState.error ? "error-message" : "success-message";
  }
}

async function loadListings(language) {
  equipmentState.loading = true;
  equipmentState.message = "";
  equipmentState.error = "";
  updateView(language);

  const params = new URLSearchParams();
  if (equipmentState.category !== "all") params.set("category", equipmentState.category);
  if (equipmentState.location.trim()) params.set("location", equipmentState.location.trim());

  try {
    const response = await fetch(`${API_BASE_URL}/api/equipment/listings?${params.toString()}`);
    if (!response.ok) throw new Error("listing load failed");
    equipmentState.listings = (await response.json()).listings ?? [];
  } catch {
    equipmentState.error = t(language, "loadError");
  } finally {
    equipmentState.loading = false;
    updateView(language);
  }
}

function openEnquiry(listingId, language) {
  equipmentState.selected = equipmentState.listings.find((item) => item.id === listingId) ?? null;
  if (!equipmentState.selected) return;
  equipmentState.enquiryOpen = true;
  equipmentState.message = "";
  equipmentState.error = "";
  updateView(language);
}

async function submitEnquiry(language) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const payload = {
    name: value("#equipment-name"),
    phone: value("#equipment-phone"),
    message: value("#equipment-message"),
  };

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/equipment/listings/${encodeURIComponent(equipmentState.selected.id)}/enquiries`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) throw new Error("enquiry failed");

    equipmentState.enquiryOpen = false;
    equipmentState.message = t(language, "enquirySent");
    equipmentState.error = "";
  } catch {
    equipmentState.error = t(language, "createError");
  }
  updateView(language);
}

function attachEvents(language) {
  const root = document.querySelector("#equipment-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-eq-category]");
    if (category) {
      equipmentState.category = category.dataset.eqCategory;
      loadListings(language);
      return;
    }

    const district = event.target.closest("[data-district]");
    if (district) {
      equipmentState.location = district.dataset.district;
      loadListings(language);
      return;
    }

    if (event.target.closest("#clear-equipment-filters")) {
      equipmentState.category = "all";
      equipmentState.location = "";
      loadListings(language);
      return;
    }

    const enquire = event.target.closest("[data-enquire]");
    if (enquire) {
      openEnquiry(enquire.dataset.enquire, language);
      return;
    }

    if (event.target.closest("#equipment-back") || event.target.closest("#equipment-cancel")) {
      equipmentState.enquiryOpen = false;
      equipmentState.selected = null;
      updateView(language);
    }
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id === "equipment-location-form") {
      event.preventDefault();
      equipmentState.location = document.querySelector("#equipment-location")?.value ?? "";
      loadListings(language);
    } else if (event.target.id === "equipment-enquiry-form") {
      event.preventDefault();
      submitEnquiry(language);
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
      <p id="equipment-status" class="success-message" role="status"></p>
      <div id="equipment-root"><div id="equipment-view">${renderView(language)}</div></div>
    </section>
  `;
}

export function initEquipment(language) {
  attachEvents(language);
  loadListings(language);
}
