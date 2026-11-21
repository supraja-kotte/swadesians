import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";

const PROFILE_ID_KEY = "agriguide.profileId";
const LOCATION_KEY = "agriguide.location";

const dashboardState = {
  loadingProfile: true,
  profile: null,
  editing: false,
  saving: false,
  saveMessage: "",
  error: "",
  weather: null,
  loadingWeather: true,
};

const selectedInterests = new Set();

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

function getProfileId() {
  try {
    let id = localStorage.getItem(PROFILE_ID_KEY);
    if (!id) {
      id = globalThis.crypto?.randomUUID?.() ?? `p-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
      localStorage.setItem(PROFILE_ID_KEY, id);
    }
    return id;
  } catch {
    return "local-profile";
  }
}

function getSavedLocation() {
  try {
    return JSON.parse(localStorage.getItem(LOCATION_KEY) ?? "null");
  } catch {
    return null;
  }
}

function conditionLabel(language, key) {
  const map = {
    clear: "condClear",
    mainly_clear: "condMainlyClear",
    partly_cloudy: "condPartlyCloudy",
    cloudy: "condCloudy",
    fog: "condFog",
    drizzle: "condDrizzle",
    rain: "condRain",
    heavy_rain: "condHeavyRain",
    thunderstorm: "condThunderstorm",
    snow: "condSnow",
  };
  return t(language, map[key] ?? "condUnknown");
}

function optionLabel(options, value, language) {
  if (!value) return "—";
  const match = options.find((option) => option.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function selectHtml(id, labelKey, options, current, language) {
  const choices = options
    .map(
      (option) =>
        `<option value="${escapeHtml(option.value)}"${option.value === current ? " selected" : ""}>${t(language, option.key)}</option>`,
    )
    .join("");

  return `
    <label class="field-label" for="${id}">${t(language, labelKey)}</label>
    <select id="${id}" class="field-input">
      <option value="">${t(language, "selectPlaceholder")}</option>
      ${choices}
    </select>
  `;
}

function renderProfileArea(language) {
  if (dashboardState.loadingProfile) {
    return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  }

  const profile = dashboardState.profile ?? {};
  const hasProfile = Boolean(profile.crop || profile.district || profile.state || profile.interests?.length);

  if (!dashboardState.editing && hasProfile) {
    const interests = (profile.interests ?? [])
      .map((code) => {
        const match = mockData.profileInterests.find((item) => item.value === code);
        return `<span class="interest-tag">${match ? t(language, match.key) : escapeHtml(code)}</span>`;
      })
      .join("");

    return `
      <div class="profile-summary">
        <div class="summary-grid">
          <div><span>${t(language, "fieldState")}</span><strong>${escapeHtml(profile.state || "—")}</strong></div>
          <div><span>${t(language, "fieldDistrict")}</span><strong>${escapeHtml(profile.district || "—")}</strong></div>
          <div><span>${t(language, "fieldCrop")}</span><strong>${escapeHtml(profile.crop || "—")}</strong></div>
          <div><span>${t(language, "fieldLandSize")}</span><strong>${optionLabel(mockData.landSizeOptions, profile.land_size, language)}</strong></div>
          <div><span>${t(language, "fieldSoilType")}</span><strong>${optionLabel(mockData.soilTypeOptions, profile.soil_type, language)}</strong></div>
          <div><span>${t(language, "fieldIrrigation")}</span><strong>${optionLabel(mockData.irrigationOptions, profile.irrigation, language)}</strong></div>
        </div>
        ${interests ? `<div class="interest-tags">${interests}</div>` : ""}
        <button type="button" id="profile-edit" class="secondary-button">${icon("edit")} ${t(language, "profileEdit")}</button>
      </div>
    `;
  }

  const chips = mockData.profileInterests
    .map(
      (item) => `
        <button type="button" class="interest-chip${selectedInterests.has(item.value) ? " is-selected" : ""}"
          data-interest="${escapeHtml(item.value)}" aria-pressed="${selectedInterests.has(item.value)}">
          ${t(language, item.key)}
        </button>
      `,
    )
    .join("");

  return `
    <p class="field-hint">${t(language, "profileOptional")}</p>
    <form id="profile-form" class="profile-form">
      <div class="form-grid">
        <div>
          <label class="field-label" for="profile-state">${t(language, "fieldState")}</label>
          <input id="profile-state" class="field-input" type="text" maxlength="60" placeholder="${t(language, "statePlaceholder")}" value="${escapeHtml(profile.state)}" />
        </div>
        <div>
          <label class="field-label" for="profile-district">${t(language, "fieldDistrict")}</label>
          <input id="profile-district" class="field-input" type="text" maxlength="60" placeholder="${t(language, "districtPlaceholder")}" value="${escapeHtml(profile.district)}" />
        </div>
        <div>
          <label class="field-label" for="profile-crop">${t(language, "fieldCrop")}</label>
          <input id="profile-crop" class="field-input" type="text" maxlength="40" placeholder="${t(language, "cropPlaceholder")}" value="${escapeHtml(profile.crop)}" />
        </div>
        ${selectHtml("profile-land", "fieldLandSize", mockData.landSizeOptions, profile.land_size, language)}
        ${selectHtml("profile-soil", "fieldSoilType", mockData.soilTypeOptions, profile.soil_type, language)}
        ${selectHtml("profile-irrigation", "fieldIrrigation", mockData.irrigationOptions, profile.irrigation, language)}
      </div>
      <fieldset class="interest-fieldset">
        <legend class="field-label">${t(language, "fieldInterests")}</legend>
        <div id="interest-chips" class="interest-chips">${chips}</div>
      </fieldset>
      <div class="form-actions">
        <button type="submit" class="primary-button"${dashboardState.saving ? " disabled" : ""}>
          ${icon("check")} ${t(language, "profileSave")}
        </button>
        ${hasProfile ? `<button type="button" id="profile-cancel" class="secondary-button">${t(language, "profileCancel")}</button>` : ""}
      </div>
    </form>
  `;
}

function renderWeatherArea(language) {
  if (dashboardState.loadingWeather) {
    return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  }

  const data = dashboardState.weather;
  const location = getSavedLocation();
  const place = location?.name || "";

  if (!data) {
    return `<div class="error-box">${t(language, "profileLoadError")}</div>`;
  }

  const current = data.current;
  const demoNote = data.is_demo
    ? `<p class="demo-badge">${t(language, "demoLabel")} — ${t(language, "demoWeatherNote")}</p>`
    : "";
  const placeLine = place
    ? t(language, "weatherFor", { place })
    : t(language, "setLocationHint");

  return `
    ${demoNote}
    <p class="weather-place">${escapeHtml(placeLine)}</p>
    <div class="snapshot-main">
      <span class="snapshot-temp">${Math.round(current.temperature)}°C</span>
      <span class="snapshot-condition">${conditionLabel(language, current.condition_key)}</span>
    </div>
    <a class="text-link" href="#/weather">${t(language, "viewWeather")} →</a>
  `;
}

const adviceMap = {
  heavy_rain: ["adviceHeavyRainTitle", "adviceHeavyRainBody"],
  rain_likely: ["adviceRainLikelyTitle", "adviceRainLikelyBody"],
  high_temperature: ["adviceHeatTitle", "adviceHeatBody"],
  strong_wind: ["adviceWindTitle", "adviceWindBody"],
  favorable: ["adviceFavorableTitle", "adviceFavorableBody"],
};

function adviceCard(language, advisory) {
  const [titleKey, bodyKey] = adviceMap[advisory.code] ?? adviceMap.favorable;
  const warningClass = advisory.severity === "warning" ? " is-warning" : "";
  return `
    <article class="advice-card${warningClass}">
      <h4>${t(language, titleKey)}</h4>
      <p>${t(language, bodyKey, advisory.values ?? {})}</p>
    </article>
  `;
}

function renderAdviceArea(language) {
  if (dashboardState.loadingWeather || !dashboardState.weather) return "";

  const advisories = dashboardState.weather.advisories ?? [];
  const warnings = advisories.filter((item) => item.severity === "warning");
  const alerts = warnings.length
    ? warnings.map((item) => adviceCard(language, item)).join("")
    : `<p>${t(language, "noAlerts")}</p>`;

  return `
    <section class="weather-section">
      <h3>${icon("bell")} ${t(language, "alertsHeading")}</h3>
      ${alerts}
    </section>
    <section class="weather-section">
      <h3>${icon("sprout")} ${t(language, "adviceHeading")}</h3>
      ${advisories.map((item) => adviceCard(language, item)).join("")}
      <p class="advice-disclaimer">${t(language, "adviceDisclaimer")}</p>
    </section>
  `;
}

function renderTeasers(language) {
  return mockData.dashboardTeasers
    .map(
      (item) => `
        <a class="teaser-card" href="${item.route}">
          <span class="teaser-icon">${icon(item.icon)}</span>
          <span class="teaser-body">
            <strong>${t(language, item.headingKey)}</strong>
            <small>${t(language, item.bodyKey)}</small>
          </span>
          <span class="phase-mini">${t(language, "plannedForPhase")} ${item.phase}</span>
        </a>
      `,
    )
    .join("");
}

function updateProfile(language) {
  const target = document.querySelector("#dashboard-profile");
  if (target) target.innerHTML = renderProfileArea(language);

  const message = document.querySelector("#profile-message");
  if (message) message.textContent = dashboardState.saveMessage;

  const error = document.querySelector("#profile-error");
  if (error) error.textContent = dashboardState.error;
}

function updateWeather(language) {
  const weatherTarget = document.querySelector("#dashboard-weather");
  if (weatherTarget) weatherTarget.innerHTML = renderWeatherArea(language);

  const adviceTarget = document.querySelector("#dashboard-advice");
  if (adviceTarget) adviceTarget.innerHTML = renderAdviceArea(language);
}

function syncInterestButtons() {
  document.querySelectorAll("[data-interest]").forEach((button) => {
    const active = selectedInterests.has(button.dataset.interest);
    button.classList.toggle("is-selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

async function loadProfile(language) {
  dashboardState.loadingProfile = true;
  updateProfile(language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/${encodeURIComponent(getProfileId())}`);
    if (!response.ok) throw new Error("profile load failed");
    const profile = await response.json();
    dashboardState.profile = profile;
    selectedInterests.clear();
    (profile.interests ?? []).forEach((item) => selectedInterests.add(item));
    dashboardState.editing = !(profile.crop || profile.district || profile.state || profile.interests?.length);
    dashboardState.error = "";
  } catch {
    dashboardState.error = t(language, "profileLoadError");
    dashboardState.editing = true;
  } finally {
    dashboardState.loadingProfile = false;
    updateProfile(language);
  }
}

async function saveProfile(language) {
  const value = (id) => document.querySelector(id)?.value ?? "";
  const payload = {
    state: value("#profile-state"),
    district: value("#profile-district"),
    crop: value("#profile-crop"),
    land_size: value("#profile-land"),
    soil_type: value("#profile-soil"),
    irrigation: value("#profile-irrigation"),
    interests: [...selectedInterests],
  };

  dashboardState.saving = true;
  dashboardState.saveMessage = "";
  dashboardState.error = "";
  updateProfile(language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/${encodeURIComponent(getProfileId())}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("profile save failed");
    dashboardState.profile = await response.json();
    dashboardState.editing = false;
    dashboardState.saveMessage = t(language, "profileSaved");
  } catch {
    dashboardState.error = t(language, "profileSaveError");
  } finally {
    dashboardState.saving = false;
    updateProfile(language);
  }
}

async function loadWeather(language) {
  dashboardState.loadingWeather = true;
  updateWeather(language);

  const params = new URLSearchParams();
  const location = getSavedLocation();
  if (location && typeof location.lat === "number" && typeof location.lon === "number") {
    params.set("lat", String(location.lat));
    params.set("lon", String(location.lon));
  }
  if (dashboardState.profile?.crop) params.set("crop", dashboardState.profile.crop);

  try {
    const response = await fetch(`${API_BASE_URL}/api/weather?${params.toString()}`);
    if (!response.ok) throw new Error("weather load failed");
    dashboardState.weather = await response.json();
  } catch {
    dashboardState.weather = null;
  } finally {
    dashboardState.loadingWeather = false;
    updateWeather(language);
  }
}

function attachEvents(language) {
  // The profile area is re-rendered after data loads, which replaces its
  // children. Delegating events to the stable container keeps them working.
  const container = document.querySelector("#dashboard-profile");
  if (!container) return;

  container.addEventListener("click", (event) => {
    if (event.target.closest("#profile-edit")) {
      selectedInterests.clear();
      (dashboardState.profile?.interests ?? []).forEach((item) => selectedInterests.add(item));
      dashboardState.editing = true;
      dashboardState.saveMessage = "";
      updateProfile(language);
      return;
    }

    if (event.target.closest("#profile-cancel")) {
      dashboardState.editing = false;
      updateProfile(language);
      return;
    }

    const chip = event.target.closest("[data-interest]");
    if (chip) {
      const code = chip.dataset.interest;
      if (selectedInterests.has(code)) selectedInterests.delete(code);
      else selectedInterests.add(code);
      syncInterestButtons();
    }
  });

  container.addEventListener("submit", (event) => {
    if (event.target.id !== "profile-form") return;
    event.preventDefault();
    saveProfile(language);
  });
}

export function renderDashboard(language) {
  return `
    <section class="dashboard-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-green">${icon("sprout")}</div>
        <div>
          <h2>${t(language, "dashboardTitle")}</h2>
          <p>${t(language, "dashboardIntro")}</p>
        </div>
      </header>

      <section class="profile-card">
        <h3>${t(language, "profileHeading")}</h3>
        <p id="profile-message" class="success-message" role="status"></p>
        <p id="profile-error" class="error-message" role="alert"></p>
        <div id="dashboard-profile">${renderProfileArea(language)}</div>
      </section>

      <section class="dashboard-weather-card">
        <h3>${icon("cloudSun")} ${t(language, "weatherSnapshot")}</h3>
        <div id="dashboard-weather">${renderWeatherArea(language)}</div>
      </section>

      <div id="dashboard-advice">${renderAdviceArea(language)}</div>

      <section class="dashboard-teasers">
        <h3>${t(language, "dashboardTitle")}</h3>
        ${renderTeasers(language)}
      </section>

      <p class="demo-footnote">${t(language, "demoTip")}: ${t(language, "demoTipBody")}</p>
      <a class="back-link" href="#/">← ${t(language, "navHome")}</a>
    </section>
  `;
}

export function initDashboard(language) {
  attachEvents(language);
  loadProfile(language).then(() => loadWeather(language));
}
