import { mockData } from "../services/mockData.js";
import { renderFeatureCard } from "../components/featureCard.js";
import { translate } from "../i18n/index.js";

export function renderHome(language) {
  const cards = mockData.features.map((feature) => renderFeatureCard(feature, language)).join("");

  return `
    <section class="home-intro">
      <h2>${translate(language, "homeTitle")}</h2>
      <p>${translate(language, "homeIntro")}</p>
      <span class="demo-badge">${translate(language, "demoData")}</span>
    </section>
    <section class="feature-grid" aria-label="Features">${cards}</section>
    <a class="admin-link" href="#/admin">${translate(language, "adminTitle")}</a>
  `;
}
