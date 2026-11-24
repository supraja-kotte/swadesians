import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";

export function renderLanguagePicker(language) {
  const pills = mockData.languages
    .map(
      (item) => `
        <button
          type="button"
          class="language-pill ${item.code === language ? "is-active" : ""}"
          data-language="${item.code}"
          aria-pressed="${item.code === language}"
        >${item.label}</button>
      `,
    )
    .join("");

  return `
    <section class="language-card" aria-label="${translate(language, "languageLabel")}">
      <p class="section-label">${translate(language, "languageLabel")}</p>
      <div class="language-pills" role="group">${pills}</div>
    </section>
  `;
}
