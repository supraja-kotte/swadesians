import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";

const marketplaceState = {
  loading: true,
  prices: [],
  category: "all",
  location: "",
  source: "",
  updatedAt: "",
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
      <div class="form-actions">
        <button type="button" id="clear-marketplace-filters" class="secondary-button">${t(language, "clearFilters")}</button>
        <button type="button" id="refresh-marketplace" class="secondary-button">${t(language, "mkRefresh")}</button>
      </div>
    </div>
  `;
}

function formatMoney(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value);
}

function renderPriceCard(language, item) {
  const price = item.modal_price ?? item.min_price ?? item.max_price;
  return `
    <article class="equipment-card">
      <div class="community-badges">
        ${badge(t(language, "mkLive"), "category")}
        ${badge(categoryLabel(language, item.category), "category")}
      </div>
      <h3>${escapeHtml(item.commodity)}</h3>
      <p class="equipment-place">${icon("mapPin")} ${escapeHtml(item.market)}, ${escapeHtml(item.district)}, ${escapeHtml(item.state)}</p>
      <p class="equipment-price">₹${formatMoney(price)} <span class="market-unit">${escapeHtml(t(language, "mkPriceUnit"))}</span></p>
      <p class="market-detail"><strong>${escapeHtml(t(language, "mkMinPrice"))}:</strong> ${formatMoney(item.min_price)} &nbsp;
        <strong>${escapeHtml(t(language, "mkMaxPrice"))}:</strong> ${formatMoney(item.max_price)}</p>
      <p class="market-detail"><strong>${escapeHtml(t(language, "mkModalPrice"))}:</strong> ${formatMoney(item.modal_price)}</p>
      <p class="market-detail"><strong>${escapeHtml(t(language, "mkArrivalDate"))}:</strong> ${escapeHtml(item.arrival_date)}</p>
      ${item.variety ? `<p class="market-detail">${escapeHtml(item.variety)}</p>` : ""}
    </article>
  `;
}

function renderList(language) {
  const cards = marketplaceState.prices.length
    ? marketplaceState.prices.map((item) => renderPriceCard(language, item)).join("")
    : `<p class="weather-status">${t(language, "mkNoPrices")}</p>`;

  return `
    ${renderFilters(language)}
    <div class="equipment-grid">${cards}</div>
    <p class="report-note">${escapeHtml(t(language, "mkNote"))}</p>
    ${
      marketplaceState.source
        ? `<p class="market-source">${escapeHtml(t(language, "mkSource"))} · ${escapeHtml(marketplaceState.updatedAt)}</p>`
        : ""
    }
  `;
}

function updateView(language) {
  const target = document.querySelector("#marketplace-view");
  if (target) {
    target.innerHTML = marketplaceState.loading
      ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
      : renderList(language);
  }

  const status = document.querySelector("#marketplace-status");
  if (status) {
    status.textContent = marketplaceState.error;
    status.className = marketplaceState.error ? "error-message" : "success-message";
  }
}

async function loadPrices(language) {
  marketplaceState.loading = true;
  marketplaceState.error = "";
  updateView(language);

  const params = new URLSearchParams();
  if (marketplaceState.category !== "all") params.set("category", marketplaceState.category);
  if (marketplaceState.location.trim()) params.set("location", marketplaceState.location.trim());

  try {
    const response = await fetch(`${API_BASE_URL}/api/marketplace/prices?${params.toString()}`);
    if (!response.ok) throw new Error("price load failed");
    const data = await response.json();
    marketplaceState.prices = data.prices ?? [];
    marketplaceState.source = data.source ?? "";
    marketplaceState.updatedAt = data.updated_at
      ? t(language, "mkUpdated", { time: data.updated_at })
      : "";
  } catch {
    marketplaceState.prices = [];
    marketplaceState.error = t(language, "mkLoadError");
  } finally {
    marketplaceState.loading = false;
    updateView(language);
  }
}

function attachEvents(language) {
  const root = document.querySelector("#marketplace-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-mk-category]");
    if (category) {
      marketplaceState.category = category.dataset.mkCategory;
      loadPrices(language);
      return;
    }

    const district = event.target.closest("[data-mk-district]");
    if (district) {
      marketplaceState.location = district.dataset.mkDistrict;
      loadPrices(language);
      return;
    }

    if (event.target.closest("#clear-marketplace-filters")) {
      marketplaceState.category = "all";
      marketplaceState.location = "";
      loadPrices(language);
      return;
    }

    if (event.target.closest("#refresh-marketplace")) loadPrices(language);
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id !== "marketplace-location-form") return;
    event.preventDefault();
    marketplaceState.location = document.querySelector("#marketplace-location")?.value ?? "";
    loadPrices(language);
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

function renderView(language) {
  return marketplaceState.loading
    ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
    : renderList(language);
}

export function initMarketplace(language) {
  attachEvents(language);
  loadPrices(language);
}
