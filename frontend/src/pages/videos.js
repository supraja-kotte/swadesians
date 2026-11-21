import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";

const videoState = {
  loading: true,
  entries: [],
  allEntries: [],
  category: "all",
  savedIds: [],
  savedLoading: true,
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
  const match = mockData.videoCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function titleFor(language, entry) {
  const content = mockData.videoContent[entry.id];
  return content ? t(language, content.title) : escapeHtml(entry.id);
}

function summaryFor(language, entry) {
  const content = mockData.videoContent[entry.id];
  return content ? t(language, content.summary) : "";
}

function renderFilters(language) {
  const chips = [
    `<button type="button" class="chip${videoState.category === "all" ? " is-selected" : ""}" data-video-category="all">${t(language, "allCategories")}</button>`,
    ...mockData.videoCategories.map(
      (item) =>
        `<button type="button" class="chip${videoState.category === item.value ? " is-selected" : ""}" data-video-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  return `<div class="community-chips">${chips}</div>`;
}

function renderEntry(language, entry) {
  const saved = videoState.savedIds.includes(entry.id);

  return `
    <article class="video-card">
      <div class="community-badges">
        <span class="community-badge demo">${t(language, "demoListing")}</span>
        <span class="community-badge category">${categoryLabel(language, entry.category)}</span>
      </div>
      <h3>${escapeHtml(titleFor(language, entry))}</h3>
      <p>${escapeHtml(summaryFor(language, entry))}</p>
      <p class="video-unavailable">${t(language, "vidNoVideo")}</p>
      <button type="button" class="${saved ? "secondary-button" : "primary-button"}" data-video-toggle="${escapeHtml(entry.id)}">
        ${saved ? icon("check") + " " + t(language, "vidSaved") : t(language, "vidSave")}
      </button>
    </article>
  `;
}

function renderSaved(language) {
  const savedEntries = videoState.allEntries.filter((entry) => videoState.savedIds.includes(entry.id));

  const list = videoState.savedLoading
    ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
    : savedEntries.length
      ? savedEntries
          .map(
            (entry) => `
            <div class="video-saved-row">
              <span>${escapeHtml(titleFor(language, entry))}</span>
              <button type="button" class="report-button" data-video-remove="${escapeHtml(entry.id)}">${t(language, "vidRemove")}</button>
            </div>
          `,
          )
          .join("")
      : `<p class="weather-status">${t(language, "vidNoSaved")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "vidMyList")}</h3>
    <p class="report-note">${t(language, "vidSaveNote")}</p>
    <div class="video-saved-list">${list}</div>
  `;
}

function updateView(language) {
  const target = document.querySelector("#videos-view");
  if (target) {
    const cards = videoState.loading
      ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
      : videoState.entries.map((entry) => renderEntry(language, entry)).join("");

    target.innerHTML = `
      <p class="equipment-note smart-disclaimer">${t(language, "videoDisclaimer")}</p>
      <section class="smart-section">
        <h3 class="smart-heading">${t(language, "videoTopicsHeading")}</h3>
        ${renderFilters(language)}
        <div class="video-grid">${cards}</div>
      </section>
      <section class="smart-section">${renderSaved(language)}</section>
    `;
  }

  const status = document.querySelector("#videos-status");
  if (status) {
    status.textContent = videoState.message || videoState.error;
    status.className = videoState.error ? "error-message" : "success-message";
  }
}

async function loadEntries(language) {
  videoState.loading = true;
  updateView(language);

  const params = new URLSearchParams();
  if (videoState.category !== "all") params.set("category", videoState.category);

  try {
    const response = await fetch(`${API_BASE_URL}/api/videos/entries?${params.toString()}`);
    if (!response.ok) throw new Error("entry load failed");
    videoState.entries = (await response.json()).entries ?? [];
    // Keep the full catalogue so "My list" can show saved items from any topic.
    if (videoState.category === "all") videoState.allEntries = videoState.entries;
  } catch {
    videoState.error = t(language, "vidLoadError");
  } finally {
    videoState.loading = false;
    updateView(language);
  }
}

async function loadSaved(language) {
  videoState.savedLoading = true;
  updateView(language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/videos/saved`);
    if (!response.ok) throw new Error("saved load failed");
    videoState.savedIds = (await response.json()).ids ?? [];
  } catch {
    videoState.error = t(language, "vidLoadError");
  } finally {
    videoState.savedLoading = false;
    updateView(language);
  }
}

async function toggleSaved(videoId, language, forceRemove = false) {
  const isSaved = videoState.savedIds.includes(videoId);
  const method = isSaved || forceRemove ? "DELETE" : "POST";

  try {
    const response = await fetch(`${API_BASE_URL}/api/videos/${encodeURIComponent(videoId)}/save`, {
      method,
    });
    if (!response.ok) throw new Error("save update failed");
    videoState.error = "";
    await loadSaved(language);
  } catch {
    videoState.error = t(language, "vidSaveError");
    updateView(language);
  }
}

function attachEvents(language) {
  const root = document.querySelector("#videos-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-video-category]");
    if (category) {
      videoState.category = category.dataset.videoCategory;
      loadEntries(language);
      return;
    }

    const toggle = event.target.closest("[data-video-toggle]");
    if (toggle) {
      toggleSaved(toggle.dataset.videoToggle, language);
      return;
    }

    const remove = event.target.closest("[data-video-remove]");
    if (remove) {
      toggleSaved(remove.dataset.videoRemove, language, true);
    }
  });
}

export function renderVideos(language) {
  return `
    <section class="videos-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-violet">${icon("video")}</div>
        <div>
          <h2>${t(language, "videosTitle")}</h2>
          <p>${t(language, "videosIntro")}</p>
        </div>
      </header>
      <p id="videos-status" class="success-message" role="status"></p>
      <div id="videos-root"><div id="videos-view">${`<p class="weather-status">${t(language, "weatherLoading")}</p>`}</div></div>
    </section>
  `;
}

export function initVideos(language) {
  attachEvents(language);
  updateView(language);
  loadEntries(language);
  loadSaved(language);
}
