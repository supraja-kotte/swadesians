import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";
import { fetchLiveWeather } from "../services/liveWeather.js";

const smartState = {
  loading: true,
  topics: [],
  category: "all",
  videos: [],
  videosLoading: true,
  error: "",
  liveWeather: null,
  weatherLoading: true,
};

// The backend stores only neutral IDs, categories and public URLs. These maps
// keep every farmer-facing word in the translated i18n files.
const VIDEO_TEXT = {
  "soil-health-campaign": { title: "sfVideoSoilHealth", source: "sfSourceIcarIiss" },
  "green-manuring": { title: "sfVideoGreenManuring", source: "sfSourceIcarNeh" },
  "soil-health-card": { title: "sfVideoSoilCard", source: "sfSourceIcarNeh" },
  "integrated-pest-management": { title: "sfVideoIpm", source: "sfSourceIcarNeh" },
  "irrigation-water-management": { title: "sfVideoIrrigation", source: "sfSourceUsda" },
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
  const match = mockData.smartTopicCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function youtubeEmbedUrl(url) {
  try {
    const parsed = new URL(url);
    const allowedHosts = new Set([
      "www.youtube.com",
      "youtube.com",
      "m.youtube.com",
      "www.youtube-nocookie.com",
    ]);
    if (!allowedHosts.has(parsed.hostname)) return "";

    const id =
      parsed.searchParams.get("v") ||
      parsed.pathname.split("/").filter(Boolean).pop() ||
      "";
    if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return "";

    return `https://www.youtube-nocookie.com/embed/${id}`;
  } catch {
    return "";
  }
}

function renderTopic(language, topic) {
  const content = mockData.smartTopicContent[topic.id];
  if (!content) return "";

  const steps = content.steps
    .map((key) => `<li>${escapeHtml(t(language, key))}</li>`)
    .join("");

  return `
    <details class="smart-topic">
      <summary>
        <span class="community-badge category">${categoryLabel(language, topic.category)}</span>
        <strong>${escapeHtml(t(language, content.title))}</strong>
      </summary>
      <ol class="smart-steps">${steps}</ol>
    </details>
  `;
}

function renderTopics(language) {
  if (smartState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;

  const chips = [
    `<button type="button" class="chip${smartState.category === "all" ? " is-selected" : ""}" data-sf-category="all">${t(language, "allCategories")}</button>`,
    ...mockData.smartTopicCategories.map(
      (item) =>
        `<button type="button" class="chip${smartState.category === item.value ? " is-selected" : ""}" data-sf-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  const cards = smartState.topics.length
    ? smartState.topics.map((topic) => renderTopic(language, topic)).join("")
    : `<p class="weather-status">${t(language, "sfNoTopics")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "smartTopicsHeading")}</h3>
    <div class="community-chips">${chips}</div>
    <div class="smart-topic-list">${cards}</div>
  `;
}

function renderVideos(language) {
  const list = smartState.videosLoading
    ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
    : smartState.videos.length
      ? smartState.videos
          .map((video) => {
            const text = VIDEO_TEXT[video.id] ?? {
              title: "sfExternalVideo",
              source: "sfWatchOnYouTube",
            };
            const title = escapeHtml(t(language, text.title));
            const embed = youtubeEmbedUrl(video.url);

            return `
              <article class="smart-video-card">
                <div class="smart-video-frame">
                  ${
                    embed
                      ? `<iframe src="${escapeHtml(embed)}" title="${title}" loading="lazy"
                           allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                           referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>`
                      : `<p class="weather-status">${t(language, "sfVideoUnavailable")}</p>`
                  }
                </div>
                <div class="smart-video-body">
                  <span class="community-badge category">${categoryLabel(language, video.category)}</span>
                  <strong>${title}</strong>
                  <span class="smart-video-source">${escapeHtml(t(language, text.source))}</span>
                  <a class="text-link" href="${escapeHtml(video.url)}" target="_blank" rel="noopener noreferrer">
                    ${escapeHtml(t(language, "sfWatchOnYouTube"))}
                  </a>
                </div>
              </article>
            `;
          })
          .join("")
      : `<p class="weather-status">${t(language, "sfNoVideos")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "smartVideosHeading")}</h3>
    <p class="report-note">${t(language, "sfVideosNote")}</p>
    <div class="smart-video-grid">${list}</div>
  `;
}

const WEATHER_LABELS = {
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

function renderLiveWeather(language) {
  let body = `<p class="weather-status">${t(language, "weatherLoading")}</p>`;

  if (!smartState.weatherLoading) {
    const data = smartState.liveWeather;
    if (!data) {
      body = `<p class="weather-status">${t(language, "weatherLocationNeeded")}</p>`;
    } else {
      const current = data.current ?? {};
      const labelKey = WEATHER_LABELS[current.condition_key] ?? "condUnknown";
      const advice = (data.advisories ?? [])
        .map((item) => `<li>${escapeHtml(t(language, adviceTitleKey(item.code)))}</li>`)
        .join("");
      body = `
        <div class="live-weather-summary">
          <strong>${Math.round(current.temperature)}°C</strong>
          <span>${escapeHtml(t(language, labelKey))}</span>
          ${data.placeName ? `<span>${escapeHtml(data.placeName)}</span>` : ""}
        </div>
        ${advice ? `<ul class="smart-steps">${advice}</ul>` : ""}
      `;
    }
  }

  return `
    <h3 class="smart-heading">${escapeHtml(t(language, "homeLiveWeather"))}</h3>
    ${body}
  `;
}

function adviceTitleKey(code) {
  return {
    heavy_rain: "adviceHeavyRainTitle",
    rain_likely: "adviceRainLikelyTitle",
    high_temperature: "adviceHeatTitle",
    strong_wind: "adviceWindTitle",
    favorable: "adviceFavorableTitle",
  }[code] ?? "adviceFavorableTitle";
}

async function loadLiveWeather(language) {
  smartState.weatherLoading = true;
  updateView(language);
  try {
    smartState.liveWeather = await fetchLiveWeather();
  } catch {
    smartState.liveWeather = null;
  } finally {
    smartState.weatherLoading = false;
    updateView(language);
  }
}

function updateView(language) {
  const target = document.querySelector("#smart-view");
  if (target) {
    target.innerHTML = `
      <p class="equipment-note smart-disclaimer">${t(language, "sfDisclaimer")}</p>
      <section class="smart-section">${renderLiveWeather(language)}</section>
      <section class="smart-section">${renderTopics(language)}</section>
      <section class="smart-section">${renderVideos(language)}</section>
    `;
  }

  const status = document.querySelector("#smart-status");
  if (status) {
    status.textContent = smartState.error;
    status.className = smartState.error ? "error-message" : "success-message";
  }
}

function queryForCategory() {
  const params = new URLSearchParams();
  if (smartState.category !== "all") params.set("category", smartState.category);
  return params.toString();
}

async function loadTopics(language) {
  smartState.loading = true;
  updateView(language);

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/smart-farming/topics?${queryForCategory()}`,
    );
    if (!response.ok) throw new Error("topic load failed");
    smartState.topics = (await response.json()).topics ?? [];
  } catch {
    smartState.error = t(language, "sfLoadError");
  } finally {
    smartState.loading = false;
    updateView(language);
  }
}

async function loadVideos(language) {
  smartState.videosLoading = true;
  updateView(language);

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/smart-farming/videos?${queryForCategory()}`,
    );
    if (!response.ok) throw new Error("video load failed");
    smartState.videos = (await response.json()).videos ?? [];
  } catch {
    smartState.error = t(language, "sfLoadError");
  } finally {
    smartState.videosLoading = false;
    updateView(language);
  }
}

function attachEvents(language) {
  const root = document.querySelector("#smart-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-sf-category]");
    if (!category) return;

    smartState.category = category.dataset.sfCategory;
    smartState.error = "";
    loadTopics(language);
    loadVideos(language);
  });
}

export function renderSmartFarming(language) {
  return `
    <section class="smart-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-green">${icon("sprout")}</div>
        <div>
          <h2>${t(language, "smartTitle")}</h2>
          <p>${t(language, "smartIntro")}</p>
        </div>
      </header>
      <p id="smart-status" class="success-message" role="status"></p>
      <div id="smart-root"><div id="smart-view">${`<p class="weather-status">${t(language, "weatherLoading")}</p>`}</div></div>
    </section>
  `;
}

export function initSmartFarming(language) {
  attachEvents(language);
  updateView(language);
  loadLiveWeather(language);
  loadTopics(language);
  loadVideos(language);
}
