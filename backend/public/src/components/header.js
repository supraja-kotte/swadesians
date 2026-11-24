import { icon } from "./icons.js";
import { translate } from "../i18n/index.js";

export function renderHeader(language) {
  const t = (key) => translate(language, key);

  return `
    <header class="app-header">
      <div class="logo-tile">${icon("sprout")}</div>
      <div>
        <h1 class="app-title">${t("appTitle")}</h1>
        <p class="app-tagline">${t("tagline")}</p>
      </div>
      <a class="header-account" href="#/login" aria-label="${t("authAccount")}">${icon("users")}<span>${t("authAccount")}</span></a>
    </header>
  `;
}
