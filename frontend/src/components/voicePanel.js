import { translate } from "../i18n/index.js";

export function renderVoicePanel(language, isOpen) {
  if (!isOpen) return "";

  const t = (key) => translate(language, key);

  return `
    <section class="voice-panel" aria-label="${t("voicePanelTitle")}">
      <div class="voice-panel-head">
        <h2>${t("voicePanelTitle")}</h2>
        <button type="button" id="voice-panel-close" class="icon-button" aria-label="Close">×</button>
      </div>
      <p class="voice-panel-desc">${t("voicePanelDesc")}</p>
      <div class="voice-panel-actions">
        <button type="button" id="read-aloud" class="primary-button">${t("readAloud")}</button>
        <button type="button" id="stop-reading" class="secondary-button">${t("stopReading")}</button>
      </div>
      <p id="speech-status" class="speech-status" role="status"></p>
    </section>
  `;
}
