import { icon } from "../components/icons.js";
import { translate } from "../i18n/index.js";

const pageIcons = {
  "#/dashboard": "sprout",
  "#/weather": "cloudSun",
  "#/schemes": "landmark",
  "#/community": "users",
  "#/smart-farming": "lightbulb",
  "#/equipment": "tractor",
  "#/marketplace": "basket",
  "#/assistant": "mic",
};

const pageKeys = {
  "#/dashboard": "cardDashboardTitle",
  "#/weather": "cardWeatherTitle",
  "#/schemes": "cardSchemesTitle",
  "#/community": "cardCommunityTitle",
  "#/smart-farming": "cardSmartFarmingTitle",
  "#/equipment": "cardEquipmentTitle",
  "#/marketplace": "cardMarketplaceTitle",
  "#/assistant": "navAssistant",
};

const pagePhases = {
  "#/dashboard": 3,
  "#/weather": 2,
  "#/schemes": 9,
  "#/community": 4,
  "#/smart-farming": 7,
  "#/equipment": 5,
  "#/marketplace": 6,
  "#/assistant": 10,
};

export function renderPlaceholder(route, language) {
  const t = (key) => translate(language, key);
  const title = t(pageKeys[route] ?? "homeTitle");
  const iconName = pageIcons[route] ?? "sprout";
  const phase = pagePhases[route] ?? "—";

  return `
    <section class="placeholder-card">
      <div class="feature-icon tone-green">${icon(iconName)}</div>
      <h2>${title}</h2>
      <p class="phase-note">${t("plannedForPhase")} ${phase}</p>
      <p>${t("comingSoon")}</p>
      <a class="back-link" href="#/">← ${t("navHome")}</a>
    </section>
  `;
}
