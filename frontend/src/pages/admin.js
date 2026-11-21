import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { adminFetch, hasSessionHint, loginAdmin, logoutAdmin } from "../services/adminAuth.js";

const adminState = {
  username: "",
  checking: false,
  loading: false,
  reports: null,
  queue: null,
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

function renderLogin(language) {
  return `
    <p class="equipment-note smart-disclaimer">${t(language, "adminDisclaimer")}</p>
    <section class="composer-card">
      <form id="admin-login-form" class="profile-form">
        <div class="form-grid">
          <div>
            <label class="field-label" for="admin-username">${t(language, "adminUsername")}</label>
            <input id="admin-username" class="field-input" type="text" autocomplete="username"
              minlength="3" maxlength="80" required />
          </div>
          <div>
            <label class="field-label" for="admin-password">${t(language, "adminPassword")}</label>
            <input id="admin-password" class="field-input" type="password" autocomplete="current-password"
              minlength="8" maxlength="200" required />
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="primary-button">${icon("check")} ${t(language, "adminSignIn")}</button>
        </div>
      </form>
    </section>
    <p class="demo-footnote">${escapeHtml(t(language, "adminHint"))}</p>
  `;
}

function renderItem(language, item, kind) {
  const isPost = kind === "posts";
  const hidden = item.status === "hidden";
  const nextStatus = hidden ? "published" : "hidden";
  const actionLabel = hidden ? t(language, "adminRestore") : t(language, "adminHide");

  return `
    <article class="admin-item">
      <div class="community-badges">
        <span class="community-badge category">${t(language, isPost ? "adminPost" : "adminReply")}</span>
        ${item.is_demo ? `<span class="community-badge demo">${escapeHtml(item.status)}</span>` : ""}
      </div>
      ${isPost && item.title ? `<strong>${escapeHtml(item.title)}</strong>` : ""}
      <p>${escapeHtml(item.body)}</p>
      <p class="report-note">${t(language, "adminReportsCount")} ${item.reports}</p>
      <button type="button" class="secondary-button"
        data-admin-action="${kind}:${escapeHtml(item.id)}:${nextStatus}">${actionLabel}</button>
    </article>
  `;
}

// Reported posts and replies need different moderation URLs, so render them
// as two collections rather than one merged list.
function renderDashboard(language) {
  if (adminState.loading || !adminState.reports || !adminState.queue) {
    return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  }

  return `
    <div class="admin-session-bar">
      <span>${t(language, "adminSignedInAs")} <strong>${escapeHtml(adminState.username)}</strong></span>
      <button type="button" id="admin-logout" class="secondary-button">${t(language, "adminSignOut")}</button>
    </div>
    <section class="smart-section">
      <h3 class="smart-heading">${t(language, "adminReports")}</h3>
      <div class="admin-items">
        ${adminState.reports.posts.length
          ? adminState.reports.posts.map((item) => renderItem(language, item, "posts")).join("")
          : `<p class="weather-status">${t(language, "adminNoReports")}</p>`}
        ${adminState.reports.replies.length
          ? adminState.reports.replies.map((item) => renderItem(language, item, "replies")).join("")
          : ""}
      </div>
    </section>
    <section class="smart-section">
      <h3 class="smart-heading">${t(language, "adminQueue")}</h3>
      <div class="admin-items">
        ${adminState.queue.posts.length
          ? adminState.queue.posts.map((item) => renderItem(language, item, "posts")).join("")
          : ""}
        ${adminState.queue.replies.length
          ? adminState.queue.replies.map((item) => renderItem(language, item, "replies")).join("")
          : ""}
        ${!adminState.queue.posts.length && !adminState.queue.replies.length
          ? `<p class="weather-status">${t(language, "adminNoQueue")}</p>`
          : ""}
      </div>
    </section>
  `;
}

function updateView(language) {
  const target = document.querySelector("#admin-view");
  if (target) {
    const signedIn = Boolean(adminState.username);
    target.innerHTML = signedIn ? renderDashboard(language) : renderLogin(language);
  }

  const status = document.querySelector("#admin-status");
  if (status) {
    status.textContent = adminState.message || adminState.error;
    status.className = adminState.error ? "error-message" : "success-message";
  }

  const form = document.querySelector("#admin-login-form");
  if (form) form.querySelectorAll("input").forEach((input) => { input.disabled = adminState.checking; });
}

function expireSession(language, showExpiryMessage = false) {
  adminState.username = "";
  adminState.checking = false;
  adminState.loading = false;
  adminState.reports = null;
  adminState.queue = null;
  adminState.error = showExpiryMessage ? t(language, "adminSessionExpired") : "";
  adminState.message = "";
  updateView(language);
}

async function loadDashboard(language) {
  adminState.loading = true;
  updateView(language);

  try {
    const [reportsResponse, queueResponse] = await Promise.all([
      adminFetch("/api/admin/reports"),
      adminFetch("/api/admin/queue"),
    ]);

    if (reportsResponse.status === 401 || queueResponse.status === 401) {
      expireSession(language, true);
      return;
    }
    if (!reportsResponse.ok || !queueResponse.ok) throw new Error("load failed");

    adminState.reports = await reportsResponse.json();
    adminState.queue = await queueResponse.json();
  } catch {
    adminState.error = t(language, "adminLoadError");
  } finally {
    adminState.loading = false;
    updateView(language);
  }
}

async function verifySession(language) {
  try {
    const response = await adminFetch("/api/admin/me");
    if (response.status === 401) {
      expireSession(language, false);
      return;
    }
    if (!response.ok) throw new Error("verify failed");

    adminState.username = (await response.json()).username ?? "";
    adminState.checking = false;
    updateView(language);
    await loadDashboard(language);
  } catch {
    adminState.error = t(language, "adminLoadError");
    adminState.checking = false;
    updateView(language);
  }
}

async function login(language) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const username = value("#admin-username");
  const password = value("#admin-password");

  adminState.checking = true;
  adminState.error = "";
  adminState.message = "";
  updateView(language);

  try {
    const body = await loginAdmin(username, password);
    adminState.username = body.username ?? username;
    adminState.checking = false;
    updateView(language);
    await loadDashboard(language);
  } catch {
    adminState.checking = false;
    adminState.error = t(language, "adminLoginError");
    updateView(language);
  }
}

async function setStatus(language, kind, id, status) {
  try {
    const response = await adminFetch(`/api/community/${kind}/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    if (response.status === 401) {
      expireSession(language, true);
      return;
    }
    if (!response.ok) throw new Error("status update failed");

    adminState.message = t(language, "adminActionDone");
    adminState.error = "";
    await loadDashboard(language);
    adminState.message = t(language, "adminActionDone");
    updateView(language);
  } catch {
    adminState.error = t(language, "adminActionError");
    updateView(language);
  }
}

async function logout(language) {
  try {
    await logoutAdmin();
  } catch {
    // Clear the visible session even if the server call fails.
  }

  adminState.username = "";
  adminState.reports = null;
  adminState.queue = null;
  adminState.message = "";
  adminState.error = "";
  updateView(language);
}

function attachEvents(language) {
  const root = document.querySelector("#admin-root");
  if (!root) return;

  root.addEventListener("submit", (event) => {
    if (event.target.id === "admin-login-form") {
      event.preventDefault();
      login(language);
    }
  });

  root.addEventListener("click", (event) => {
    if (event.target.closest("#admin-logout")) {
      logout(language);
      return;
    }

    const action = event.target.closest("[data-admin-action]");
    if (action) {
      const [kind, id, status] = action.dataset.adminAction.split(":");
      setStatus(language, kind, id, status);
    }
  });
}

export function renderAdmin(language) {
  return `
    <section class="admin-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-green">${icon("users")}</div>
        <div>
          <h2>${t(language, "adminTitle")}</h2>
          <p>${t(language, "adminIntro")}</p>
        </div>
      </header>
      <p id="admin-status" class="success-message" role="status"></p>
      <div id="admin-root"><div id="admin-view">${`<p class="weather-status">${t(language, "weatherLoading")}</p>`}</div></div>
    </section>
  `;
}

export function initAdmin(language) {
  attachEvents(language);
  updateView(language);
  if (hasSessionHint()) verifySession(language);
}
