import { mockData } from "../services/mockData.js";
import { renderFeatureCard } from "../components/featureCard.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { fetchLiveWeather } from "../services/liveWeather.js";

const homeWeather = { loading: true, data: null, error: "" };

const conditionKeys = {
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

function t(language, key) {
  return translate(language, key);
}

function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function renderWeatherStrip(language) {
  if (homeWeather.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  if (!homeWeather.data) {
    return `<p class="weather-status">${escapeHtml(homeWeather.error || t(language, "weatherLocationNeeded"))}</p>`;
  }

  const current = homeWeather.data.current ?? {};
  const conditionKey = conditionKeys[current.condition_key] ?? "condUnknown";
  const place = homeWeather.data.placeName;

  return `
    <div class="home-weather-row">
      <span class="home-weather-icon">${icon("cloudSun")}</span>
      <div>
        <strong>${Math.round(current.temperature)}°C</strong>
        <span>${escapeHtml(t(language, conditionKey))}</span>
        ${place ? `<span class="home-weather-place">${escapeHtml(place)}</span>` : ""}
      </div>
      <a class="text-link" href="#/weather">${escapeHtml(t(language, "viewWeather"))} →</a>
    </div>
  `;
}

function updateWeather(language) {
  const target = document.querySelector("#home-weather");
  if (target) target.innerHTML = renderWeatherStrip(language);
}

export function renderHome(language) {
  const cards = mockData.features.map((feature) => renderFeatureCard(feature, language)).join("");

  return `
    <section class="home-intro">
      <h2>${translate(language, "homeTitle")}</h2>
      <p>${translate(language, "homeIntro")}</p>
    </section>
    <section class="home-live-weather">
      <h3>${escapeHtml(t(language, "homeLiveWeather"))}</h3>
      <div id="home-weather">${renderWeatherStrip(language)}</div>
    </section>
    <section class="feature-grid" aria-label="Features">${cards}</section>
    <a class="admin-link" href="#/admin">${translate(language, "adminTitle")}</a>
  `;
}

export async function initHome(language) {
  homeWeather.loading = true;
  homeWeather.error = "";
  homeWeather.data = null;
  updateWeather(language);

  try {
    homeWeather.data = await fetchLiveWeather();
  } catch {
    homeWeather.error = t(language, "weatherError");
  } finally {
    homeWeather.loading = false;
    updateWeather(language);
  }
}
