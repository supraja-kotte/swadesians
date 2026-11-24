import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";

const schemeState = {
  loading: true,
  topics: [],
  category: "all",
  links: [],
  linksLoading: true,
  linkFilter: "all",
  questions: [],
  questionsLoading: true,
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
  const match = mockData.schemeCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function renderTopic(language, topic) {
  const content = mockData.schemeContent[topic.id];
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
  if (schemeState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;

  const chips = [
    `<button type="button" class="chip${schemeState.category === "all" ? " is-selected" : ""}" data-sch-category="all">${t(language, "allCategories")}</button>`,
    ...mockData.schemeCategories.map(
      (item) =>
        `<button type="button" class="chip${schemeState.category === item.value ? " is-selected" : ""}" data-sch-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  const cards = schemeState.topics.length
    ? schemeState.topics.map((topic) => renderTopic(language, topic)).join("")
    : `<p class="weather-status">${t(language, "schNoQuestions")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "schemeTopicsHeading")}</h3>
    <div class="community-chips">${chips}</div>
    <div class="smart-topic-list">${cards}</div>
  `;
}

const linkFilters = [
  { value: "all", key: "schLinkFilterAll" },
  { value: "central", key: "schLinkCentral" },
  { value: "Andhra Pradesh", key: "schLinkStateAP" },
  { value: "Telangana", key: "schLinkStateTS" },
];

function renderLinkCard(language, link) {
  const levelLabel = link.level === "central" ? "schLinkLabelCentral" : "schLinkLabelState";
  const stateBadge = link.state
    ? `<span class="community-badge category">${escapeHtml(link.state)}</span>`
    : "";

  return `
    <article class="scheme-link-card">
      <div class="community-badges">
        <span class="community-badge demo">${t(language, levelLabel)}</span>
        ${stateBadge}
      </div>
      <strong>${escapeHtml(link.name)}</strong>
      <p class="scheme-link-meta">
        ${t(language, "schLinkOfficialDomain")}: ${escapeHtml(link.sourceDomain)}
        &nbsp;·&nbsp; ${t(language, "schLinkVerified")} ${escapeHtml(link.verifiedOn)}
      </p>
      <a class="secondary-button scheme-link-button" href="${escapeHtml(link.url)}"
        target="_blank" rel="noopener noreferrer">${t(language, "schLinkOpen")}</a>
    </article>
  `;
}

function renderLinks(language) {
  const chips = linkFilters
    .map(
      (item) =>
        `<button type="button" class="chip${schemeState.linkFilter === item.value ? " is-selected" : ""}"
          data-sch-link-filter="${escapeHtml(item.value)}">${t(language, item.key)}</button>`,
    )
    .join("");

  const list = schemeState.linksLoading
    ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
    : schemeState.links.length
      ? schemeState.links.map((link) => renderLinkCard(language, link)).join("")
      : `<p class="weather-status">${t(language, "schNoLinks")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "schLinksHeading")}</h3>
    <p class="report-note">${t(language, "schLinksIntro")}</p>
    <div class="community-chips">${chips}</div>
    <div class="scheme-link-list">${list}</div>
  `;
}

function renderQuestions(language) {
  const list = schemeState.questionsLoading
    ? `<p class="weather-status">${t(language, "weatherLoading")}</p>`
    : schemeState.questions.length
      ? schemeState.questions
          .map(
            (item) => `
            <article class="smart-note scheme-question">
              <span>${escapeHtml(item.question)}</span>
              <button type="button" class="report-button" data-sch-delete="${escapeHtml(item.id)}">${t(language, "schRemove")}</button>
            </article>
          `,
          )
          .join("")
      : `<p class="weather-status">${t(language, "schNoQuestions")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "schMyQuestions")}</h3>
    <p class="report-note">${t(language, "schQuestionsNote")}</p>
    <section class="composer-card">
      <form id="scheme-question-form" class="profile-form">
        <label class="field-label" for="scheme-question">${t(language, "schQuestionLabel")}</label>
        <textarea id="scheme-question" class="field-input" rows="2" minlength="3" maxlength="300"
          placeholder="${t(language, "schQuestionPlaceholder")}" required></textarea>
        <div class="form-actions">
          <button type="submit" class="primary-button">${icon("check")} ${t(language, "schAddQuestion")}</button>
        </div>
      </form>
    </section>
    <div class="smart-note-list">${list}</div>
  `;
}

function updateView(language) {
  const target = document.querySelector("#scheme-view");
  if (target) {
    target.innerHTML = `
      <p class="equipment-note smart-disclaimer">${t(language, "schemeDisclaimer")}</p>
      <section class="smart-section">${renderLinks(language)}</section>
      <section class="smart-section">${renderTopics(language)}</section>
      <section class="smart-section">${renderQuestions(language)}</section>
    `;
  }

  const status = document.querySelector("#scheme-status");
  if (status) {
    status.textContent = schemeState.message || schemeState.error;
    status.className = schemeState.error ? "error-message" : "success-message";
  }
}

async function loadTopics(language) {
  schemeState.loading = true;
  updateView(language);

  const params = new URLSearchParams();
  if (schemeState.category !== "all") params.set("category", schemeState.category);

  try {
    const response = await fetch(`${API_BASE_URL}/api/schemes/topics?${params.toString()}`);
    if (!response.ok) throw new Error("topic load failed");
    schemeState.topics = (await response.json()).topics ?? [];
  } catch {
    schemeState.error = t(language, "schLoadError");
  } finally {
    schemeState.loading = false;
    updateView(language);
  }
}

async function loadLinks(language) {
  schemeState.linksLoading = true;
  updateView(language);

  const params = new URLSearchParams();
  if (schemeState.linkFilter !== "all") {
    if (schemeState.linkFilter === "central") params.set("level", "central");
    else {
      params.set("level", "state");
      params.set("state", schemeState.linkFilter);
    }
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/schemes/links?${params.toString()}`);
    if (!response.ok) throw new Error("link load failed");
    schemeState.links = (await response.json()).links ?? [];
  } catch {
    schemeState.error = t(language, "schLoadError");
    schemeState.links = [];
  } finally {
    schemeState.linksLoading = false;
    updateView(language);
  }
}

async function loadQuestions(language) {
  schemeState.questionsLoading = true;
  updateView(language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/schemes/questions`);
    if (!response.ok) throw new Error("question load failed");
    schemeState.questions = (await response.json()).questions ?? [];
  } catch {
    schemeState.error = t(language, "schLoadError");
  } finally {
    schemeState.questionsLoading = false;
    updateView(language);
  }
}

async function addQuestion(language) {
  const input = document.querySelector("#scheme-question");
  const question = input?.value ?? "";

  try {
    const response = await fetch(`${API_BASE_URL}/api/schemes/questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) throw new Error("question save failed");

    schemeState.message = t(language, "schQuestionSaved");
    schemeState.error = "";
    if (input) input.value = "";
    await loadQuestions(language);
    schemeState.message = t(language, "schQuestionSaved");
    updateView(language);
  } catch {
    schemeState.error = t(language, "schCreateError");
    updateView(language);
  }
}

async function deleteQuestion(questionId, language) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/schemes/questions/${encodeURIComponent(questionId)}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("question delete failed");

    schemeState.message = t(language, "schQuestionDeleted");
    schemeState.error = "";
    await loadQuestions(language);
    schemeState.message = t(language, "schQuestionDeleted");
    updateView(language);
  } catch {
    schemeState.error = t(language, "schCreateError");
    updateView(language);
  }
}

function attachEvents(language) {
  const root = document.querySelector("#scheme-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-sch-category]");
    if (category) {
      schemeState.category = category.dataset.schCategory;
      loadTopics(language);
      return;
    }

    const linkFilter = event.target.closest("[data-sch-link-filter]");
    if (linkFilter) {
      schemeState.linkFilter = linkFilter.dataset.schLinkFilter;
      loadLinks(language);
      return;
    }

    const remove = event.target.closest("[data-sch-delete]");
    if (remove) {
      deleteQuestion(remove.dataset.schDelete, language);
    }
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id === "scheme-question-form") {
      event.preventDefault();
      addQuestion(language);
    }
  });
}

export function renderSchemes(language) {
  return `
    <section class="schemes-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-green">${icon("landmark")}</div>
        <div>
          <h2>${t(language, "schemesTitle")}</h2>
          <p>${t(language, "schemesIntro")}</p>
        </div>
      </header>
      <p id="scheme-status" class="success-message" role="status"></p>
      <div id="scheme-root"><div id="scheme-view">${`<p class="weather-status">${t(language, "weatherLoading")}</p>`}</div></div>
    </section>
  `;
}

export function initSchemes(language) {
  attachEvents(language);
  updateView(language);
  loadTopics(language);
  loadLinks(language);
  loadQuestions(language);
}
