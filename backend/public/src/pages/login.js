import { translate } from "../i18n/index.js";
import { setFlashMessage, refreshApp } from "../state.js";
import { icon } from "../components/icons.js";
import { adminFetch, hasSessionHint as hasAdminSession, loginAdmin, logoutAdmin } from "../services/adminAuth.js";
import {
  farmerFetch,
  hasFarmerSession,
  loginFarmer,
  logoutFarmer,
  registerFarmer,
} from "../services/farmerAuth.js";

const authState = {
  role: "farmer",
  mode: "login",
  checking: false,
  redirecting: false,
  identity: null,
  message: "",
  error: "",
  form: { username: "", password: "", displayName: "", confirm: "" },
};

// Sign-in moves straight into the app after a short success beat. Keep the
// timer cancellable so navigation or sign-out never triggers a late redirect.
let redirectTimer = 0;

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

function roleHasSession(role) {
  return role === "farmer" ? hasFarmerSession() : hasAdminSession();
}

function clearForm() {
  authState.form = { username: "", password: "", displayName: "", confirm: "" };
}

function destinationForRole(role) {
  return role === "farmer" ? "#/dashboard" : "#/admin";
}

export function cancelAuthRedirect() {
  if (redirectTimer) {
    window.clearTimeout(redirectTimer);
    redirectTimer = 0;
  }
  authState.redirecting = false;
}

function scheduleRedirect(language, destination) {
  cancelAuthRedirect();
  authState.redirecting = true;
  authState.checking = true;
  setFlashMessage(authState.message);
  updateView(language);

  redirectTimer = window.setTimeout(() => {
    redirectTimer = 0;
    authState.redirecting = false;
    window.location.hash = destination;
  }, 750);
}

function renderRoleTabs(language) {
  return `
    <div class="auth-tabs" role="tablist" aria-label="${escapeHtml(t(language, "authTitle"))}">
      <button type="button" role="tab" class="auth-tab ${authState.role === "farmer" ? "is-active" : ""}"
        aria-selected="${authState.role === "farmer"}" data-auth-role="farmer">
        ${icon("sprout")} ${escapeHtml(t(language, "authRoleFarmer"))}
      </button>
      <button type="button" role="tab" class="auth-tab ${authState.role === "admin" ? "is-active" : ""}"
        aria-selected="${authState.role === "admin"}" data-auth-role="admin">
        ${icon("users")} ${escapeHtml(t(language, "authRoleAdmin"))}
      </button>
    </div>
  `;
}

function renderModeSwitch(language) {
  if (authState.role !== "farmer") return "";

  return `
    <div class="auth-mode-switch" aria-label="${escapeHtml(t(language, "authModeLogin"))}">
      <button type="button" class="auth-mode ${authState.mode === "login" ? "is-active" : ""}"
        aria-pressed="${authState.mode === "login"}" data-auth-mode="login">
        ${escapeHtml(t(language, "authModeLogin"))}
      </button>
      <button type="button" class="auth-mode ${authState.mode === "register" ? "is-active" : ""}"
        aria-pressed="${authState.mode === "register"}" data-auth-mode="register">
        ${escapeHtml(t(language, "authModeRegister"))}
      </button>
    </div>
  `;
}

function renderForm(language) {
  const isRegister = authState.role === "farmer" && authState.mode === "register";
  const noteKey = authState.role === "farmer" ? "authFarmerNote" : "authAdminNote";
  const passwordHint = isRegister
    ? `<p class="field-hint">${escapeHtml(t(language, "authRegisterHint"))}</p>`
    : "";

  return `
    <p class="auth-note">${escapeHtml(t(language, noteKey))}</p>
    <form id="auth-form" class="profile-form">
      <div class="form-grid">
        <div>
          <label class="field-label" for="auth-username">${escapeHtml(t(language, "authUsername"))}</label>
          <input id="auth-username" class="field-input" type="text" autocomplete="username"
            minlength="3" maxlength="80" required
            value="${escapeHtml(authState.form.username)}" />
        </div>
        ${isRegister ? `
          <div>
            <label class="field-label" for="auth-display-name">${escapeHtml(t(language, "authDisplayName"))}</label>
            <input id="auth-display-name" class="field-input" type="text" autocomplete="name"
              maxlength="60" value="${escapeHtml(authState.form.displayName)}" />
          </div>
        ` : ""}
        <div>
          <label class="field-label" for="auth-password">${escapeHtml(t(language, "authPassword"))}</label>
          <input id="auth-password" class="field-input" type="password"
            autocomplete="${authState.role === "farmer" && isRegister ? "new-password" : "current-password"}"
            minlength="8" maxlength="200" required
            value="${escapeHtml(authState.form.password)}" />
          ${passwordHint}
        </div>
        ${isRegister ? `
          <div>
            <label class="field-label" for="auth-confirm-password">${escapeHtml(t(language, "authConfirmPassword"))}</label>
            <input id="auth-confirm-password" class="field-input" type="password"
              autocomplete="new-password" minlength="8" maxlength="200" required
              value="${escapeHtml(authState.form.confirm)}" />
          </div>
        ` : ""}
      </div>
      <div class="form-actions">
        <button type="submit" class="primary-button" ${authState.checking ? "disabled" : ""}>
          ${icon("check")}
          ${escapeHtml(t(language, isRegister ? "authCreateAccount" : "authSignIn"))}
        </button>
      </div>
    </form>
    ${authState.role === "admin"
      ? `<p class="auth-note auth-hint">${escapeHtml(t(language, "adminHint"))}</p>`
      : ""}
  `;
}

function renderSession(language) {
  const isFarmer = authState.identity.role === "farmer";
  const destination = destinationForRole(authState.identity.role);
  const actionKey = isFarmer ? "authGoDashboard" : "authGoAdmin";
  const transitioning = authState.redirecting;

  return `
    <section class="auth-session-card${transitioning ? " is-transitioning" : ""}" ${transitioning ? 'aria-busy="true"' : ""}>
      <p class="success-message">${escapeHtml(authState.message)}</p>
      <p>${escapeHtml(t(language, "authSignedInAs"))}
        <strong>${escapeHtml(authState.identity.name)}</strong>
        <span class="auth-role-badge">${escapeHtml(t(language, isFarmer ? "authRoleFarmer" : "authRoleAdmin"))}</span>
      </p>
      ${transitioning ? '<div class="auth-progress" aria-hidden="true"><span></span></div>' : ""}
      <div class="form-actions">
        <a class="primary-button" data-auth-open href="${destination}">${escapeHtml(t(language, actionKey))}</a>
        <button type="button" id="auth-signout" class="secondary-button" ${authState.checking ? "disabled" : ""}>
          ${escapeHtml(t(language, "authSignOut"))}
        </button>
      </div>
    </section>
  `;
}

function updateView(language) {
  const target = document.querySelector("#auth-root");
  if (!target) return;

  const status = document.querySelector("#auth-status");
  if (status) {
    status.textContent = authState.error;
    status.className = authState.error ? "error-message" : "success-message";
  }

  target.innerHTML = authState.identity
    ? renderSession(language)
    : `${renderRoleTabs(language)}<section class="composer-card auth-card">
        ${renderModeSwitch(language)}
        ${renderForm(language)}
      </section>`;
}

async function verifyRole(language, role) {
  if (!roleHasSession(role)) {
    authState.identity = null;
    updateView(language);
    return;
  }

  authState.checking = true;
  authState.error = "";
  updateView(language);

  try {
    const response = role === "farmer"
      ? await farmerFetch("/api/farmer/me")
      : await adminFetch("/api/admin/me");

    if (response.status === 401) {
      authState.identity = null;
    } else if (response.ok) {
      const body = await response.json();
      authState.identity = {
        role,
        name: role === "farmer" ? (body.display_name ?? body.username) : body.username,
      };
    } else {
      throw new Error("verify failed");
    }
  } catch {
    authState.identity = null;
    authState.error = t(language, "authError");
  } finally {
    authState.checking = false;
    updateView(language);
  }
}

async function submit(language) {
  if (authState.checking) return;

  const isRegister = authState.role === "farmer" && authState.mode === "register";
  const role = authState.role;
  const username = authState.form.username.trim();
  const password = authState.form.password;

  if (isRegister && password !== authState.form.confirm) {
    authState.error = t(language, "authPasswordMismatch");
    updateView(language);
    return;
  }

  authState.checking = true;
  authState.error = "";
  authState.message = "";
  updateView(language);

  let signedIn = false;
  try {
    let body;
    if (role === "admin") {
      body = await loginAdmin(username, password);
    } else if (isRegister) {
      body = await registerFarmer(username, password, authState.form.displayName.trim());
    } else {
      body = await loginFarmer(username, password);
    }

    authState.identity = {
      role,
      name: body.display_name ?? body.username ?? username,
    };
    authState.message = t(language, isRegister || role === "farmer" ? "authSuccessFarmer" : "authSuccessAdmin");
    clearForm();
    signedIn = true;
  } catch {
    authState.error = t(language, "authError");
  } finally {
    authState.checking = false;
    updateView(language);
    if (signedIn) scheduleRedirect(language, destinationForRole(role));
  }
}

async function signOut(language) {
  if (!authState.identity || authState.checking) return;

  cancelAuthRedirect();
  authState.checking = true;
  updateView(language);

  try {
    if (authState.identity.role === "farmer") await logoutFarmer();
    else await logoutAdmin();
  } catch {
    // Clear the visible session even if the server call fails.
  }

  authState.identity = null;
  authState.mode = "login";
  authState.message = "";
  authState.error = "";
  authState.checking = false;
  updateView(language);
  refreshApp();
}

function attachEvents(language) {
  const root = document.querySelector("#auth-root");
  if (!root) return;

  root.addEventListener("input", (event) => {
    const id = event.target.id;
    if (id === "auth-username") authState.form.username = event.target.value;
    if (id === "auth-password") authState.form.password = event.target.value;
    if (id === "auth-display-name") authState.form.displayName = event.target.value;
    if (id === "auth-confirm-password") authState.form.confirm = event.target.value;
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id !== "auth-form") return;
    event.preventDefault();
    submit(language);
  });

  root.addEventListener("click", (event) => {
    const roleButton = event.target.closest("[data-auth-role]");
    if (roleButton) {
      cancelAuthRedirect();
      authState.role = roleButton.dataset.authRole;
      authState.mode = "login";
      authState.identity = null;
      authState.error = "";
      authState.message = "";
      clearForm();
      updateView(language);
      verifyRole(language, authState.role);
      return;
    }

    const modeButton = event.target.closest("[data-auth-mode]");
    if (modeButton) {
      authState.mode = modeButton.dataset.authMode;
      authState.error = "";
      clearForm();
      updateView(language);
      return;
    }

    if (event.target.closest("[data-auth-open]")) cancelAuthRedirect();
    if (event.target.closest("#auth-signout")) signOut(language);
  });
}

export function renderLoginPage(language) {
  return `
    <section class="auth-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-green">${icon("users")}</div>
        <div>
          <h2>${escapeHtml(t(language, "authTitle"))}</h2>
          <p>${escapeHtml(t(language, "authIntro"))}</p>
        </div>
      </header>
      <p id="auth-status" class="success-message" role="status"></p>
      <div id="auth-root"><p class="weather-status">${escapeHtml(t(language, "weatherLoading"))}</p></div>
    </section>
  `;
}

export function initLoginPage(language) {
  cancelAuthRedirect();
  attachEvents(language);
  const initialRole = hasFarmerSession() ? "farmer" : hasAdminSession() ? "admin" : "farmer";
  authState.role = initialRole;
  authState.mode = "login";
  authState.identity = null;
  authState.error = "";
  authState.message = "";
  clearForm();
  updateView(language);

  if (roleHasSession(initialRole)) verifyRole(language, initialRole);
}
