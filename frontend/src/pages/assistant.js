import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";
import { speak, stopSpeaking } from "../services/speech.js";
import { isRecognitionSupported, createRecognizer } from "../services/speechRecognition.js";

const assistantState = {
  loading: true,
  commands: [],
  category: "all",
  listening: false,
  heard: "",
  lastAction: "",
  error: "",
  aiAvailable: false,
  asking: false,
  answer: "",
};

let recognizer = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function t(language, key) {
  return translate(language, key);
}

function categoryLabel(language, value) {
  const match = mockData.voiceCommandCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function phraseFor(language, command) {
  const content = mockData.voiceCommandContent[command.id];
  return content ? t(language, content.phraseKey) : "";
}

function renderCommands(language) {
  if (assistantState.loading) return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;

  const chips = [
    `<button type="button" class="chip${assistantState.category === "all" ? " is-selected" : ""}" data-as-category="all">${t(language, "allCategories")}</button>`,
    ...mockData.voiceCommandCategories.map(
      (item) =>
        `<button type="button" class="chip${assistantState.category === item.value ? " is-selected" : ""}" data-as-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  const cards = assistantState.commands.length
    ? assistantState.commands
        .map(
          (command) => `
          <article class="voice-command-card">
            <span class="community-badge category">${categoryLabel(language, command.category)}</span>
            <strong>${escapeHtml(phraseFor(language, command))}</strong>
          </article>
        `,
        )
        .join("")
    : `<p class="weather-status">${t(language, "assistantLoadError")}</p>`;

  return `
    <h3 class="smart-heading">${t(language, "assistantCommandsHeading")}</h3>
    <div class="community-chips">${chips}</div>
    <div class="voice-command-grid">${cards}</div>
  `;
}

function updateView(language) {
  const target = document.querySelector("#assistant-view");
  if (target) {
    const supported = isRecognitionSupported();
    const ai = assistantState.aiAvailable;
    const statusLines = [
      assistantState.listening ? `<p class="weather-status">${t(language, "assistantListening")}</p>` : "",
      assistantState.heard ? `<p class="report-note">${t(language, "assistantHeard")} ${escapeHtml(assistantState.heard)}</p>` : "",
      assistantState.lastAction ? `<p class="report-note">${t(language, "assistantLastAction")} ${escapeHtml(assistantState.lastAction)}</p>` : "",
      assistantState.asking ? `<p class="weather-status">${t(language, "assistantAsking")}</p>` : "",
      !supported ? `<p class="equipment-note smart-disclaimer">${t(language, "assistantNotSupported")}</p>` : "",
    ]
      .filter(Boolean)
      .join("");

    const answerCard = assistantState.answer
      ? `<section class="ai-answer-card">
           <h3 class="smart-heading">${t(language, "assistantAnswerHeading")}</h3>
           <p class="ai-answer-text">${escapeHtml(assistantState.answer)}</p>
           <button type="button" id="assistant-replay" class="secondary-button">
             ${icon("mic")} ${t(language, "assistantReplay")}
           </button>
           <p class="report-note">${t(language, "assistantVoiceNote")}</p>
         </section>`
      : "";

    target.innerHTML = `
      <p class="equipment-note smart-disclaimer">${t(language, ai ? "assistantAiDisclaimer" : "assistantDisclaimer")}</p>
      <section class="assistant-controls">
        <p class="report-note">${t(language, ai ? "assistantAiIntro" : "assistantIntro")}</p>
        <button type="button" id="assistant-mic" class="primary-button${assistantState.listening ? " is-listening" : ""}" ${supported ? "" : "disabled"}>
          ${icon("mic")} ${t(language, assistantState.listening ? "assistantStop" : "assistantStart")}
        </button>
        <form id="assistant-type-form" class="profile-form">
          <label class="field-label" for="assistant-type">${t(language, ai ? "assistantAskLabel" : "assistantTypeLabel")}</label>
          <div class="assistant-type-row">
            <input id="assistant-type" class="field-input" type="text" maxlength="500"
              placeholder="${t(language, ai ? "assistantAskPlaceholder" : "assistantTypePlaceholder")}" />
            <button type="submit" class="secondary-button">${t(language, ai ? "assistantAskButton" : "assistantGo")}</button>
          </div>
        </form>
      </section>
      <div id="assistant-live" role="status">${statusLines}</div>
      ${answerCard}
      <section class="smart-section">${renderCommands(language)}</section>
    `;
  }

  const status = document.querySelector("#assistant-status");
  if (status) {
    status.textContent = assistantState.error;
    status.className = assistantState.error ? "error-message" : "success-message";
  }
}

async function loadConfig(language) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/assistant/config`);
    if (!response.ok) throw new Error("config load failed");
    assistantState.aiAvailable = Boolean((await response.json()).available);
  } catch {
    assistantState.aiAvailable = false;
  }

  const intro = document.querySelector("#assistant-intro");
  if (intro) {
    intro.textContent = t(language, assistantState.aiAvailable ? "assistantAiIntro" : "assistantIntro");
  }
  updateView(language);
}

async function askAI(language, text) {
  if (!text.trim()) return;

  assistantState.asking = true;
  assistantState.answer = "";
  assistantState.error = "";
  stopListening();
  updateView(language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/assistant/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.trim(), language }),
    });
    if (!response.ok) throw new Error("ask failed");

    const data = await response.json();
    assistantState.answer = data.answer ?? "";
    speak(assistantState.answer, language);
  } catch {
    assistantState.error = t(language, "assistantAskError");
  } finally {
    assistantState.asking = false;
    if (document.querySelector("#assistant-root")) updateView(language);
  }
}

async function loadCommands(language) {
  assistantState.loading = true;
  updateView(language);

  const params = new URLSearchParams();
  if (assistantState.category !== "all") params.set("category", assistantState.category);

  try {
    const response = await fetch(`${API_BASE_URL}/api/assistant/commands?${params.toString()}`);
    if (!response.ok) throw new Error("command load failed");
    assistantState.commands = (await response.json()).commands ?? [];
  } catch {
    assistantState.error = t(language, "assistantLoadError");
  } finally {
    assistantState.loading = false;
    updateView(language);
  }
}

function matchCommand(language, transcript) {
  const normalized = transcript.toLowerCase().trim();
  const rules = assistantState.commands
    .map((command) => {
      const content = mockData.voiceCommandContent[command.id];
      const phrase = content ? t(language, content.phraseKey).toLowerCase().trim() : "";
      return { command, content, phrase };
    })
    .filter((rule) => rule.phrase)
    .sort((a, b) => b.phrase.length - a.phrase.length);

  return rules.find((rule) => normalized.includes(rule.phrase)) ?? null;
}

function executeCommand(language, match) {
  // If the farmer navigated away while speech was being processed, do nothing.
  if (!document.querySelector("#assistant-root")) return;

  const { command, content } = match;

  if (command.category === "navigation" && content.route) {
    assistantState.lastAction = phraseFor(language, command);
    assistantState.error = "";
    stopListening();
    updateView(language);
    window.location.hash = content.route;
    return;
  }

  if (content.action === "read") {
    const text = document.querySelector("#page-content")?.innerText ?? "";
    const supported = speak(text, language);
    assistantState.lastAction = supported ? t(language, "assistantReadStarted") : "";
    assistantState.error = supported ? "" : t(language, "assistantNotSupported");
  } else if (content.action === "stop") {
    stopSpeaking();
    assistantState.lastAction = t(language, "assistantStopped");
    assistantState.error = "";
  } else if (content.action === "help") {
    const supported = speak(t(language, "assistantHelpSpoken"), language);
    assistantState.lastAction = supported ? t(language, "vcHelp") : "";
    assistantState.error = supported ? "" : t(language, "assistantNotSupported");
  }
}

async function handlePhrase(language, transcript) {
  assistantState.heard = transcript;
  const match = matchCommand(language, transcript);

  if (!match) {
    if (assistantState.aiAvailable) {
      await askAI(language, transcript);
      return;
    }
    assistantState.error = t(language, "assistantNoMatch");
    updateView(language);
    return;
  }

  assistantState.error = "";
  executeCommand(language, match);
  if (document.querySelector("#assistant-root")) updateView(language);
}

function stopListening() {
  if (recognizer) {
    try {
      recognizer.stop();
    } catch {
      // The engine may already have stopped.
    }
    recognizer = null;
  }
  assistantState.listening = false;
}

function toggleListening(language) {
  if (assistantState.listening) {
    stopListening();
    updateView(language);
    return;
  }

  recognizer = createRecognizer({
    language,
    onResult: (transcript) => {
      stopListening();
      handlePhrase(language, transcript);
    },
    onError: () => {
      stopListening();
      assistantState.error = t(language, "assistantMicError");
      updateView(language);
    },
    onEnd: () => {
      assistantState.listening = false;
      updateView(language);
    },
  });

  if (!recognizer) {
    assistantState.error = t(language, "assistantNotSupported");
    updateView(language);
    return;
  }

  assistantState.listening = true;
  assistantState.error = "";
  updateView(language);

  try {
    recognizer.start();
  } catch {
    stopListening();
    assistantState.error = t(language, "assistantMicError");
    updateView(language);
  }
}

function attachEvents(language) {
  const root = document.querySelector("#assistant-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-as-category]");
    if (category) {
      assistantState.category = category.dataset.asCategory;
      loadCommands(language);
      return;
    }

    if (event.target.closest("#assistant-mic")) {
      toggleListening(language);
      return;
    }

    if (event.target.closest("#assistant-replay") && assistantState.answer) {
      speak(assistantState.answer, language);
    }
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id !== "assistant-type-form") return;
    event.preventDefault();
    const input = document.querySelector("#assistant-type");
    const value = input?.value ?? "";
    if (input) input.value = "";
    handlePhrase(language, value);
  });
}

export function renderAssistant(language) {
  return `
    <section class="assistant-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-violet">${icon("mic")}</div>
        <div>
          <h2>${t(language, "assistantTitle")}</h2>
          <p id="assistant-intro">${t(language, "assistantIntro")}</p>
        </div>
      </header>
      <p id="assistant-status" class="success-message" role="status"></p>
      <div id="assistant-root"><div id="assistant-view">${`<p class="weather-status">${t(language, "weatherLoading")}</p>`}</div></div>
    </section>
  `;
}

export function initAssistant(language) {
  stopListening();
  attachEvents(language);
  updateView(language);
  loadConfig(language);
  loadCommands(language);
}
