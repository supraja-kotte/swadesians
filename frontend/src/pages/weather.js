import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";
import { state as appState } from "../state.js";

const LOCATION_KEY = "agriguide.location";

const weatherState = {
  loading: false,
  error: "",
  data: null,
  lat: null,
  lon: null,
  placeName: "",
  crop: "",
  places: [],
  searching: false,
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

function condition(language, key) {
  const map = {
    clear: ["condClear", "sun"],
    mainly_clear: ["condMainlyClear", "sun"],
    partly_cloudy: ["condPartlyCloudy", "cloudSun"],
    cloudy: ["condCloudy", "cloud"],
    fog: ["condFog", "fog"],
    drizzle: ["condDrizzle", "rain"],
    rain: ["condRain", "rain"],
    heavy_rain: ["condHeavyRain", "rain"],
    thunderstorm: ["condThunderstorm", "storm"],
    snow: ["condSnow", "cloud"],
  };
  const [labelKey, iconName] = map[key] ?? ["condUnknown", "cloudSun"];
  return { label: t(language, labelKey), icon: icon(iconName) };
}

const adviceMap = {
  heavy_rain: ["adviceHeavyRainTitle", "adviceHeavyRainBody"],
  rain_likely: ["adviceRainLikelyTitle", "adviceRainLikelyBody"],
  high_temperature: ["adviceHeatTitle", "adviceHeatBody"],
  strong_wind: ["adviceWindTitle", "adviceWindBody"],
  favorable: ["adviceFavorableTitle", "adviceFavorableBody"],
};

function saveLocation() {
  try {
    localStorage.setItem(
      LOCATION_KEY,
      JSON.stringify({ lat: weatherState.lat, lon: weatherState.lon, name: weatherState.placeName }),
    );
  } catch {
    // Storage is optional.
  }
}

function restoreLocation() {
  try {
    const saved = JSON.parse(localStorage.getItem(LOCATION_KEY) ?? "null");
    if (saved && typeof saved.lat === "number" && typeof saved.lon === "number") {
      weatherState.lat = saved.lat;
      weatherState.lon = saved.lon;
      weatherState.placeName = saved.name ?? "";
    }
  } catch {
    // Ignore invalid saved data.
  }
}

function renderPlaceList(language) {
  if (weatherState.searching) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  if (weatherState.places.length === 0) return "";

  return `
    <div class="place-list">
      ${weatherState.places
        .map(
          (place) => `
            <button type="button" class="place-button" data-lat="${place.latitude}" data-lon="${place.longitude}" data-name="${escapeHtml(place.name)}">
              ${escapeHtml(place.name)}${place.admin1 ? `, ${escapeHtml(place.admin1)}` : ""}
            </button>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderControls(language) {
  const quickPlaces = mockData.weatherQuickPlaces
    .map((name) => `<button type="button" class="chip quick-place" data-name="${escapeHtml(name)}">${escapeHtml(name)}</button>`)
    .join("");

  return `
    <section class="location-card">
      <h2 class="section-heading">${t(language, "weatherTitle")}</h2>
      <div class="location-actions">
        <button type="button" id="use-location" class="primary-button">${t(language, "useMyLocation")}</button>
        <button type="button" id="weather-refresh" class="secondary-button">${t(language, "refreshWeather")}</button>
      </div>
      <form id="place-search-form" class="search-row">
        <label class="visually-hidden" for="place-input">${t(language, "placeSearchHint")}</label>
        <input id="place-input" type="search" placeholder="${t(language, "placeSearchHint")}" value="${escapeHtml(weatherState.placeName)}" />
        <button type="submit" class="primary-button">${t(language, "searchButton")}</button>
      </form>
      <div class="quick-places">${quickPlaces}</div>
      <div id="place-list">${renderPlaceList(language)}</div>
      <label class="crop-label" for="crop-input">${t(language, "cropOptional")}</label>
      <input id="crop-input" type="text" maxlength="40" placeholder="${t(language, "cropPlaceholder")}" value="${escapeHtml(weatherState.crop)}" />
      <p id="selected-place" class="selected-place">${weatherState.placeName ? `${t(language, "selectedPlace")}: ${escapeHtml(weatherState.placeName)}` : ""}</p>
    </section>
  `;
}

function renderAdvice(language, advisory) {
  const [titleKey, bodyKey] = adviceMap[advisory.code] ?? adviceMap.favorable;
  const warningClass = advisory.severity === "warning" ? " is-warning" : "";

  return `
    <article class="advice-card${warningClass}">
      <h3>${t(language, titleKey)}</h3>
      <p>${t(language, bodyKey, advisory.values ?? {})}</p>
    </article>
  `;
}

function renderWeatherBody(language) {
  if (weatherState.loading) {
    return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  }
  if (weatherState.error) {
    return `<div class="error-box">${escapeHtml(weatherState.error)}</div>`;
  }

  const data = weatherState.data;
  if (!data) return "";

  const current = data.current;
  const today = data.daily?.[0] ?? {};
  const currentCondition = condition(language, current.condition_key);
  const hourly = (data.hourly ?? [])
    .map(
      (hour) => `
        <div class="hour-item">
          <span class="hour-time">${escapeHtml(hour.time)}</span>
          <span class="hour-icon">${condition(language, hour.condition_key).icon}</span>
          <strong>${Math.round(hour.temperature)}°</strong>
          <span class="rain-chance">${Math.round(hour.rain_chance)}%</span>
        </div>
      `,
    )
    .join("");

  const daily = (data.daily ?? [])
    .map(
      (day) => `
        <div class="daily-row">
          <span class="daily-date">${escapeHtml(day.date)}</span>
          <span class="hour-icon">${condition(language, day.condition_key).icon}</span>
          <span class="daily-temps">${Math.round(day.min)}° / ${Math.round(day.max)}°</span>
          <span class="rain-chance">${Math.round(day.rain_chance)}% · ${day.rainfall} mm</span>
        </div>
      `,
    )
    .join("");

  const warnings = (data.advisories ?? []).filter((item) => item.severity === "warning");
  const warningHtml = warnings.length
    ? warnings.map((item) => renderAdvice(language, item)).join("")
    : `<p>${t(language, "noWarnings")}</p>`;

  const adviceHtml = (data.advisories ?? []).map((item) => renderAdvice(language, item)).join("");

  return `
    <section class="current-card">
      <div class="current-main">
        <div class="current-icon">${currentCondition.icon}</div>
        <div>
          <p class="current-temp">${Math.round(current.temperature)}°C</p>
          <p class="current-condition">${currentCondition.label}</p>
        </div>
      </div>
      <div class="metric-grid">
        <div class="metric"><span>${t(language, "feelsLike")}</span><strong>${Math.round(current.feels_like)}°C</strong></div>
        <div class="metric"><span>${t(language, "humidity")}</span><strong>${Math.round(current.humidity)}%</strong></div>
        <div class="metric"><span>${t(language, "rainfall")}</span><strong>${current.precipitation} mm</strong></div>
        <div class="metric"><span>${t(language, "windSpeed")}</span><strong>${Math.round(current.wind_speed)} km/h</strong></div>
        <div class="metric"><span>${t(language, "sunrise")}</span><strong>${escapeHtml(today.sunrise ?? "—")}</strong></div>
        <div class="metric"><span>${t(language, "sunset")}</span><strong>${escapeHtml(today.sunset ?? "—")}</strong></div>
      </div>
    </section>

    <section class="weather-section">
      <h3>${t(language, "hourlyForecast")}</h3>
      <div class="hourly-strip">${hourly}</div>
    </section>

    <section class="weather-section">
      <h3>${t(language, "dailyForecast")}</h3>
      <div class="daily-list">${daily}</div>
    </section>

    <section class="weather-section">
      <h3>${t(language, "weatherWarnings")}</h3>
      ${warningHtml}
    </section>

    <section class="weather-section">
      <h3>${t(language, "farmAdvice")}</h3>
      ${adviceHtml}
      <p class="advice-disclaimer">${t(language, "adviceDisclaimer")}</p>
    </section>

    <p class="source-note">${t(language, "sourceLabel")}: ${escapeHtml(data.source)}</p>
  `;
}

function updateContent(language) {
  const target = document.querySelector("#weather-content");
  if (target) target.innerHTML = renderWeatherBody(language);
}

function updatePlaces(language) {
  const target = document.querySelector("#place-list");
  if (target) target.innerHTML = renderPlaceList(language);
}

function updateSelectedPlace(language) {
  const label = document.querySelector("#selected-place");
  if (label) {
    label.textContent = weatherState.placeName
      ? `${t(language, "selectedPlace")}: ${weatherState.placeName}`
      : "";
  }
  const input = document.querySelector("#place-input");
  if (input) input.value = weatherState.placeName;
}

async function loadWeather(language) {
  weatherState.loading = true;
  weatherState.error = "";
  updateContent(language);

  if (weatherState.lat === null || weatherState.lon === null) {
    weatherState.data = null;
    weatherState.error = t(language, "weatherLocationNeeded");
    weatherState.loading = false;
    updateContent(language);
    return;
  }

  const params = new URLSearchParams();
  params.set("lat", String(weatherState.lat));
  params.set("lon", String(weatherState.lon));
  if (weatherState.crop.trim()) params.set("crop", weatherState.crop.trim());

  try {
    const response = await fetch(`${API_BASE_URL}/api/weather?${params.toString()}`);
    if (!response.ok) throw new Error("weather request failed");
    weatherState.data = await response.json();
  } catch {
    weatherState.error = t(appState.language, "weatherError");
  } finally {
    weatherState.loading = false;
    updateContent(appState.language);
  }
}

async function searchPlaces(name) {
  if (!name || name.trim().length < 2) return;
  weatherState.searching = true;
  updatePlaces(appState.language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/weather/places?name=${encodeURIComponent(name.trim())}`);
    const body = await response.json();
    weatherState.places = body.results ?? [];
  } catch {
    weatherState.places = [];
  } finally {
    weatherState.searching = false;
    updatePlaces(appState.language);
  }
}

function selectPlace(place) {
  weatherState.lat = place.lat;
  weatherState.lon = place.lon;
  weatherState.placeName = place.name;
  weatherState.places = [];
  weatherState.searching = false;
  weatherState.error = "";
  updatePlaces(appState.language);
  updateSelectedPlace(appState.language);
  saveLocation();
  loadWeather(appState.language);
}

function useMyLocation() {
  if (!navigator.geolocation) {
    weatherState.error = t(appState.language, "locationDenied");
    updateContent(appState.language);
    return;
  }

  weatherState.loading = true;
  updateContent(appState.language);

  navigator.geolocation.getCurrentPosition(
    (position) => {
      weatherState.lat = position.coords.latitude;
      weatherState.lon = position.coords.longitude;
      weatherState.placeName = t(appState.language, "useMyLocation");
      weatherState.error = "";
      updateSelectedPlace(appState.language);
      saveLocation();
      loadWeather(appState.language);
    },
    () => {
      weatherState.loading = false;
      weatherState.error = t(appState.language, "locationDenied");
      updateContent(appState.language);
    },
    { timeout: 10000, maximumAge: 600000 },
  );
}

export function renderWeather(language) {
  return `
    <section class="weather-page">
      ${renderControls(language)}
      <div id="weather-content">${renderWeatherBody(language)}</div>
    </section>
  `;
}

export function initWeather() {
  restoreLocation();

  document.querySelector("#use-location")?.addEventListener("click", useMyLocation);
  document.querySelector("#weather-refresh")?.addEventListener("click", () => loadWeather(appState.language));

  document.querySelector("#place-search-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = document.querySelector("#place-input");
    searchPlaces(input?.value ?? "");
  });

  document.querySelector("#place-list")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-lat]");
    if (!button) return;
    selectPlace({
      lat: Number(button.dataset.lat),
      lon: Number(button.dataset.lon),
      name: button.dataset.name,
    });
  });

  document.querySelector(".quick-places")?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-name]");
    if (!button) return;
    const name = button.dataset.name;
    const input = document.querySelector("#place-input");
    if (input) input.value = name;
    await searchPlaces(name);
    if (weatherState.places.length > 0) {
      selectPlace({
        lat: weatherState.places[0].latitude,
        lon: weatherState.places[0].longitude,
        name: weatherState.places[0].name,
      });
    }
  });

  document.querySelector("#crop-input")?.addEventListener("change", (event) => {
    weatherState.crop = event.target.value;
    loadWeather(appState.language);
  });

  loadWeather(appState.language);
}
