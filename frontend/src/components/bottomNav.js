import { icon } from "./icons.js";
import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";

export function renderBottomNav(language, route) {
  const links = mockData.nav
    .map((item) => {
      const active = item.route === route;
      return `
        <a class="nav-item ${active ? "is-active" : ""}" href="${item.route}" ${active ? 'aria-current="page"' : ""}>
          ${icon(item.icon)}
          <span>${translate(language, item.key)}</span>
        </a>
      `;
    })
    .join("");

  return `<nav class="bottom-nav" aria-label="Primary"><div class="bottom-nav-inner">${links}</div></nav>`;
}
