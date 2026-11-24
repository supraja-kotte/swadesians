// A very small shared state store. Pages read from it, and app.js redraws the
// screen whenever something changes. No framework is needed for this.

import { supportedLanguages } from "./i18n/index.js";

const STORAGE_KEY = "agriguide.language";

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
