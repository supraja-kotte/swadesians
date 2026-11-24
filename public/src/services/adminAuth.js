// Session tokens are now HttpOnly cookies, so JavaScript cannot read them.
// A readable CSRF cookie is echoed back in the X-CSRF-Token header on writes.
// Old localStorage tokens from earlier phases are removed on load.

import { API_BASE_URL } from "../config.js";

const CSRF_COOKIE = "agriguide_csrf";
const HINT_COOKIE = "agriguide_admin_hint";
const LEGACY_TOKEN_KEY = "agriguide.adminToken";
const MUTATING_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

let csrfFromLogin = "";

try {
  localStorage.removeItem(LEGACY_TOKEN_KEY);
} catch {
  // Storage may be blocked; the cookie session still works.
}

function readCookie(name) {
  const prefix = `${name}=`;
  const found = document.cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith(prefix));
  return found ? decodeURIComponent(found.slice(prefix.length)) : "";
}

export function getCsrfToken() {
  return csrfFromLogin || readCookie(CSRF_COOKIE);
}

export function hasSessionHint() {
  return readCookie(HINT_COOKIE) === "1";
}

export async function loginAdmin(username, password) {
  const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error("login failed");

  const body = await response.json();
  csrfFromLogin = body.csrfToken ?? "";
  return body;
}

export async function adminFetch(path, options = {}) {
  const headers = { ...(options.headers ?? {}) };
  const method = (options.method ?? "GET").toUpperCase();

  if (MUTATING_METHODS.includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) headers["X-CSRF-Token"] = csrfToken;
  }
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });
}

export async function logoutAdmin() {
  return adminFetch("/api/admin/logout", { method: "POST" });
}
