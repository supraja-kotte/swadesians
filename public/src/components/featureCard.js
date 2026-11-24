import { icon } from "./icons.js";
import { translate } from "../i18n/index.js";

export function renderFeatureCard(feature, language) {
  const t = (key) => translate(language, key);

  return `
    <a class="feature-card" href="${feature.route}">
      <div class="feature-card-top">
        <div class="feature-icon tone-${feature.tone}">${icon(feature.icon)}</div>
        <span class="feature-chevron">${icon("chevron")}</span>
      </div>
      <div class="feature-text">
        <h2>${t(feature.titleKey)}</h2>
        <p>${t(feature.descKey)}</p>
      </div>
    </a>
  `;
}
