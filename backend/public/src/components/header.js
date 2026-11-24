import { icon } from "./icons.js";
import { translate } from "../i18n/index.js";
import { hasFarmerSession } from "../services/farmerAuth.js";
import { hasSessionHint as hasAdminSession } from "../services/adminAuth.js";

export function renderHeader(language) {
  const t = (key) => translate(language, key);
  const farmerSignedIn = hasFarmerSession();
  const adminSignedIn = !farmerSignedIn && hasAdminSession();
  const accountHref = farmerSignedIn ? "#/dashboard" : adminSignedIn ? "#/admin" : "#/login";
  const accountLabel = farmerSignedIn
    ? t("dashboardTitle")
    : adminSignedIn
      ? t("authRoleAdmin")
      : t("authAccount");
  const accountClass = farmerSignedIn || adminSignedIn ? "header-account is-signed-in" : "header-account";

  return `
    <header class="app-header">
      <div class="logo-tile">${icon("sprout")}</div>
      <div>
        <h1 class="app-title">${t("appTitle")}</h1>
        <p class="app-tagline">${t("tagline")}</p>
      </div>
      <a class="${accountClass}" href="${accountHref}" aria-label="${accountLabel}">${icon("users")}<span>${accountLabel}</span></a>
    </header>
  `;
}
