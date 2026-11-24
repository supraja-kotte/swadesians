import { icon } from "./icons.js";
import { translate } from "../i18n/index.js";

export function renderVoiceButton(language) {
  return `
    <button type="button" id="voice-button" class="voice-fab" aria-label="${translate(language, "voiceButton")}" title="${translate(language, "voiceButton")}">
      ${icon("mic")}
    </button>
  `;
}
