// Farmer sessions use their own HttpOnly cookie and CSRF token, separate from
// administrator sessions so signing in as one role cannot overwrite the other.

import { API_BASE_URL } from "../config.js";

const CSRF_COOKIE = "agriguide_farmer_csrf";
const HINT_COOKIE = "agriguide_farmer_hint";
const MUTATING_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

let csrfFromLogin = "";

function readCookie(name) {
  const prefix = `${name}=`;
  const found = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(prefix));
  return found ? decodeURIComponent(found.slice(prefix.length)) : "";
}

export function getFarmerCsrfToken() {
  return csrfFromLogin || readCookie(CSRF_COOKIE);
}

export function hasFarmerSession() {
  return readCookie(HINT_COOKIE) === "1";
}

async function readError(response) {
  try {
    const body = await response.json();
    return body.detail || "Request failed";
  } catch {
    return "Request failed";
  }
}

async function authenticate(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await readError(response));

  const body = await response.json();
  csrfFromLogin = body.csrfToken ?? "";
  return body;
}

export function registerFarmer(username, password, displayName = "") {
  return authenticate("/api/farmer/register", { username, password, display_name: displayName });
}

export function loginFarmer(username, password) {
  return authenticate("/api/farmer/login", { username, password });
}

export async function farmerFetch(path, options = {}) {
  const headers = { ...(options.headers ?? {}) };
  const method = (options.method ?? "GET").toUpperCase();

  if (MUTATING_METHODS.includes(method)) {
    const csrfToken = getFarmerCsrfToken();
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

export async function logoutFarmer() {
  return farmerFetch("/api/farmer/logout", { method: "POST" });
}
