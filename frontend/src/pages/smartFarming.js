import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";

const smartState = {
  loading: true,
  topics: [],
  category: "all",
  notes: [],
  notesLoading: true,
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
  const match = mockData.smartTopicCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function formatDate(iso) {
  return iso ? String(iso).slice(0, 10) : "";
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
    : `<p class="weather-status">${t(language, "sfNoNotes")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "smartTopicsHeading")}</h3>
    <div class="community-chips">${chips}</div>
    <div class="smart-topic-list">${cards}</div>
  `;
}

function renderNotes(language) {
  const list = smartState.notesLoading
    ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
    : smartState.notes.length
      ? smartState.notes
          .map(
            (note) => `
            <article class="smart-note">
              <strong>${escapeHtml(note.field_name)} — ${escapeHtml(note.crop)}</strong>
              ${note.stage ? `<span class="community-badge category">${escapeHtml(note.stage)}</span>` : ""}
              ${note.observation ? `<p>${escapeHtml(note.observation)}</p>` : ""}
              <span class="smart-note-date">${formatDate(note.created_at)}</span>
            </article>
          `,
          )
          .join("")
      : `<p class="weather-status">${t(language, "sfNoNotes")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "smartNotesHeading")}</h3>
    <p class="report-note">${t(language, "sfNotesNote")}</p>
    <section class="composer-card">
      <form id="smart-note-form" class="profile-form">
        <div class="form-grid">
          <div>
            <label class="field-label" for="smart-field">${t(language, "sfFieldName")}</label>
            <input id="smart-field" class="field-input" type="text" minlength="2" maxlength="60"
              placeholder="${t(language, "sfFieldPlaceholder")}" required />
          </div>
          <div>
            <label class="field-label" for="smart-crop">${t(language, "sfCrop")}</label>
            <input id="smart-crop" class="field-input" type="text" minlength="2" maxlength="60"
              placeholder="${t(language, "sfCropPlaceholder")}" required />
          </div>
          <div>
            <label class="field-label" for="smart-stage">${t(language, "sfStage")}</label>
            <input id="smart-stage" class="field-input" type="text" maxlength="40"
              placeholder="${t(language, "sfStagePlaceholder")}" />
          </div>
        </div>
        <label class="field-label" for="smart-observation">${t(language, "sfObservation")}</label>
        <textarea id="smart-observation" class="field-input" rows="3" maxlength="500"
          placeholder="${t(language, "sfObservationPlaceholder")}"></textarea>
        <div class="form-actions">
          <button type="submit" class="primary-button">${icon("check")} ${t(language, "sfSaveNote")}</button>
        </div>
      </form>
    </section>
    <div class="smart-note-list">${list}</div>
  `;
}

function updateView(language) {
  const target = document.querySelector("#smart-view");
  if (target) {
    target.innerHTML = `
      <p class="equipment-note smart-disclaimer">${t(language, "sfDisclaimer")}</p>
      <section class="smart-section">${renderTopics(language)}</section>
      <section class="smart-section">${renderNotes(language)}</section>
    `;
  }

  const status = document.querySelector("#smart-status");
  if (status) {
    status.textContent = smartState.message || smartState.error;
    status.className = smartState.error ? "error-message" : "success-message";
  }
}

async function loadTopics(language) {
  smartState.loading = true;
  updateView(language);

  const params = new URLSearchParams();
  if (smartState.category !== "all") params.set("category", smartState.category);

  try {
    const response = await fetch(`${API_BASE_URL}/api/smart-farming/topics?${params.toString()}`);
    if (!response.ok) throw new Error("topic load failed");
    smartState.topics = (await response.json()).topics ?? [];
  } catch {
    smartState.error = t(language, "sfLoadError");
  } finally {
    smartState.loading = false;
    updateView(language);
  }
}

async function loadNotes(language) {
  smartState.notesLoading = true;
  updateView(language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/smart-farming/notes`);
    if (!response.ok) throw new Error("note load failed");
    smartState.notes = (await response.json()).notes ?? [];
  } catch {
    smartState.error = t(language, "sfLoadError");
  } finally {
    smartState.notesLoading = false;
    updateView(language);
  }
}

async function saveNote(language) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const payload = {
    field_name: value("#smart-field"),
    crop: value("#smart-crop"),
    stage: value("#smart-stage"),
    observation: value("#smart-observation"),
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/smart-farming/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("note save failed");

    smartState.message = t(language, "sfNoteSaved");
    smartState.error = "";
    await loadNotes(language);
    smartState.message = t(language, "sfNoteSaved");
    updateView(language);
  } catch {
    smartState.error = t(language, "sfCreateError");
    updateView(language);
  }
}

function attachEvents(language) {
  const root = document.querySelector("#smart-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-sf-category]");
    if (category) {
      smartState.category = category.dataset.sfCategory;
      loadTopics(language);
    }
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id === "smart-note-form") {
      event.preventDefault();
      saveNote(language);
    }
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
  loadTopics(language);
  loadNotes(language);
}
