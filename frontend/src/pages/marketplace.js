import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";

const marketplaceState = {
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
  const match = mockData.marketplaceCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function badge(text, className = "") {
  return `<span class="community-badge ${className}">${escapeHtml(text)}</span>`;
}

function renderFilters(language) {
  const chips = [
    `<button type="button" class="chip${marketplaceState.category === "all" ? " is-selected" : ""}" data-mk-category="all">${t(language, "allCategories")}</button>`,
    ...mockData.marketplaceCategories.map(
      (item) =>
        `<button type="button" class="chip${marketplaceState.category === item.value ? " is-selected" : ""}" data-mk-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  const districts = mockData.marketplaceDistricts
    .map(
      (name) =>
        `<button type="button" class="chip district-chip" data-mk-district="${escapeHtml(name)}">${escapeHtml(name)}</button>`,
    )
    .join("");

  return `
    <div class="equipment-filters">
      <div class="community-chips">${chips}</div>
      <form id="marketplace-location-form" class="search-row">
        <label class="visually-hidden" for="marketplace-location">${t(language, "locationLabel")}</label>
        <input id="marketplace-location" type="search" maxlength="60"
          placeholder="${t(language, "locationPlaceholder")}" value="${escapeHtml(marketplaceState.location)}" />
        <button type="submit" class="primary-button">${t(language, "searchButton")}</button>
      </form>
      <div class="quick-places">${districts}</div>
      <button type="button" id="clear-marketplace-filters" class="secondary-button">${t(language, "clearFilters")}</button>
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
      <p class="market-detail"><strong>${t(language, "mkQuantity")}:</strong> ${escapeHtml(item.quantity_label)}</p>
      <p class="market-detail"><strong>${t(language, "mkMarket")}:</strong> ${escapeHtml(item.market_hint)}</p>
      <p class="equipment-price">${t(language, "priceUnavailable")}</p>
      <button type="button" class="primary-button" data-mk-enquire="${escapeHtml(item.id)}">${t(language, "mkEnquire")}</button>
    </article>
  `;
}

function renderList(language) {
  const cards = marketplaceState.listings.length
    ? marketplaceState.listings.map((item) => renderListingCard(language, item)).join("")
    : `<p class="weather-status">${t(language, "mkNoListings")}</p>`;

  return `
    ${renderFilters(language)}
    <div class="equipment-grid">${cards}</div>
  `;
}

function renderEnquiry(language) {
  const item = marketplaceState.selected;
  if (!item) return "";

  return `
    <div class="equipment-enquiry">
      <button type="button" id="marketplace-back" class="secondary-button">${t(language, "mkBackToListings")}</button>
      <article class="equipment-card is-selected">
        <div class="community-badges">
          ${badge(t(language, "demoListing"), "demo")}
          ${badge(categoryLabel(language, item.category), "category")}
        </div>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="equipment-place">${icon("mapPin")} ${escapeHtml(item.district)}, ${escapeHtml(item.state)}</p>
      </article>
      <section class="composer-card">
        <h3>${t(language, "mkEnquiryHeading")}</h3>
        <p class="equipment-note">${t(language, "mkEnquiryNote")}</p>
        <form id="marketplace-enquiry-form" class="profile-form">
          <label class="field-label" for="marketplace-name">${t(language, "mkName")}</label>
          <input id="marketplace-name" class="field-input" type="text" minlength="2" maxlength="60" required />
          <label class="field-label" for="marketplace-phone">${t(language, "fieldPhone")}</label>
          <input id="marketplace-phone" class="field-input" type="tel" minlength="7" maxlength="20"
            placeholder="${t(language, "phonePlaceholder")}" required />
          <label class="field-label" for="marketplace-quantity">${t(language, "mkQuantityLabel")}</label>
          <input id="marketplace-quantity" class="field-input" type="text" maxlength="60"
            placeholder="${t(language, "mkQuantityPlaceholder")}" />
          <label class="field-label" for="marketplace-message">${t(language, "fieldMessage")}</label>
          <textarea id="marketplace-message" class="field-input" rows="3" maxlength="500"
            placeholder="${t(language, "mkMessagePlaceholder")}"></textarea>
          <div class="form-actions">
            <button type="submit" class="primary-button">${icon("check")} ${t(language, "mkSendEnquiry")}</button>
            <button type="button" id="marketplace-cancel" class="secondary-button">${t(language, "cancel")}</button>
          </div>
        </form>
      </section>
    </div>
  `;
}

function renderView(language) {
  if (marketplaceState.enquiryOpen) return renderEnquiry(language);
  if (marketplaceState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  return renderList(language);
}

function updateView(language) {
  const target = document.querySelector("#marketplace-view");
  if (target) target.innerHTML = renderView(language);

  const status = document.querySelector("#marketplace-status");
  if (status) {
    status.textContent = marketplaceState.message || marketplaceState.error;
    status.className = marketplaceState.error ? "error-message" : "success-message";
  }
}

async function loadListings(language) {
  marketplaceState.loading = true;
  marketplaceState.message = "";
  marketplaceState.error = "";
  updateView(language);

  const params = new URLSearchParams();
  if (marketplaceState.category !== "all") params.set("category", marketplaceState.category);
  if (marketplaceState.location.trim()) params.set("location", marketplaceState.location.trim());

  try {
    const response = await fetch(`${API_BASE_URL}/api/marketplace/listings?${params.toString()}`);
    if (!response.ok) throw new Error("listing load failed");
    marketplaceState.listings = (await response.json()).listings ?? [];
  } catch {
    marketplaceState.error = t(language, "mkLoadError");
  } finally {
    marketplaceState.loading = false;
    updateView(language);
  }
}

function openEnquiry(listingId, language) {
  marketplaceState.selected = marketplaceState.listings.find((item) => item.id === listingId) ?? null;
  if (!marketplaceState.selected) return;
  marketplaceState.enquiryOpen = true;
  marketplaceState.message = "";
  marketplaceState.error = "";
  updateView(language);
}

async function submitEnquiry(language) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const payload = {
    name: value("#marketplace-name"),
    phone: value("#marketplace-phone"),
    quantity: value("#marketplace-quantity"),
    message: value("#marketplace-message"),
  };

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/marketplace/listings/${encodeURIComponent(marketplaceState.selected.id)}/enquiries`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) throw new Error("enquiry failed");

    marketplaceState.enquiryOpen = false;
    marketplaceState.message = t(language, "mkEnquirySent");
    marketplaceState.error = "";
  } catch {
    marketplaceState.error = t(language, "mkCreateError");
  }
  updateView(language);
}

function attachEvents(language) {
  const root = document.querySelector("#marketplace-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-mk-category]");
    if (category) {
      marketplaceState.category = category.dataset.mkCategory;
      loadListings(language);
      return;
    }

    const district = event.target.closest("[data-mk-district]");
    if (district) {
      marketplaceState.location = district.dataset.mkDistrict;
      loadListings(language);
      return;
    }

    if (event.target.closest("#clear-marketplace-filters")) {
      marketplaceState.category = "all";
      marketplaceState.location = "";
      loadListings(language);
      return;
    }

    const enquire = event.target.closest("[data-mk-enquire]");
    if (enquire) {
      openEnquiry(enquire.dataset.mkEnquire, language);
      return;
    }

    if (event.target.closest("#marketplace-back") || event.target.closest("#marketplace-cancel")) {
      marketplaceState.enquiryOpen = false;
      marketplaceState.selected = null;
      updateView(language);
    }
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id === "marketplace-location-form") {
      event.preventDefault();
      marketplaceState.location = document.querySelector("#marketplace-location")?.value ?? "";
      loadListings(language);
    } else if (event.target.id === "marketplace-enquiry-form") {
      event.preventDefault();
      submitEnquiry(language);
    }
  });
}

export function renderMarketplace(language) {
  return `
    <section class="marketplace-page equipment-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-amber">${icon("basket")}</div>
        <div>
          <h2>${t(language, "marketplaceTitle")}</h2>
          <p>${t(language, "marketplaceIntro")}</p>
        </div>
      </header>
      <p id="marketplace-status" class="success-message" role="status"></p>
      <div id="marketplace-root"><div id="marketplace-view">${renderView(language)}</div></div>
    </section>
  `;
}

export function initMarketplace(language) {
  attachEvents(language);
  loadListings(language);
}
