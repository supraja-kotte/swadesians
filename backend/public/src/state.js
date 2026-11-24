// A very small shared state store. Pages read from it, and app.js redraws the
// screen whenever something changes. No framework is needed for this.

import { supportedLanguages } from "./i18n/index.js";

const STORAGE_KEY = "agriguide.language";
const FLASH_KEY = "agriguide.flashMessage";

export const state = {
  language: "en",
  route: "#/",
  voicePanelOpen: false,
};

const listeners = new Set();

function notify() {
  listeners.forEach((listener) => listener());
}

export function subscribe(listener) {
  listeners.add(listener);
}

export function initState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && supportedLanguages.includes(saved)) {
      state.language = saved;
    }
  } catch {
    // Some browsers block local storage. The app still works with defaults.
  }
  state.route = window.location.hash || "#/";
}

export function setLanguage(language) {
  if (!supportedLanguages.includes(language) || language === state.language) return;

  state.language = language;
  state.voicePanelOpen = false;

  try {
    localStorage.setItem(STORAGE_KEY, language);
  } catch {
    // Ignore storage errors.
  }

  notify();
}

export function setRoute(route) {
  if (route === state.route) return;
  state.route = route;
  state.voicePanelOpen = false;
  notify();
}

export function toggleVoicePanel() {
  state.voicePanelOpen = !state.voicePanelOpen;
  notify();
}

export function closeVoicePanel() {
  if (!state.voicePanelOpen) return;
  state.voicePanelOpen = false;
  notify();
}

// A signed-in user is taken straight into the app. The destination page shows
// this one-time message so the hand-off feels intentional instead of abrupt.
export function setFlashMessage(message) {
  try {
    sessionStorage.setItem(FLASH_KEY, message);
  } catch {
    // Session storage may be blocked; navigation still works without the toast.
  }
}

export function consumeFlashMessage() {
  try {
    const message = sessionStorage.getItem(FLASH_KEY) ?? "";
    if (message) sessionStorage.removeItem(FLASH_KEY);
    return message;
  } catch {
    return "";
  }
}

export function refreshApp() {
  notify();
}
