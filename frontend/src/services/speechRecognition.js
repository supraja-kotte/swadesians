// Browser speech recognition. This uses the device's own speech engine and a
// fixed keyword list — it is NOT an AI service and sends audio nowhere.
// Supported in Chrome/Edge; other browsers can use the typing fallback.

import { voiceLang } from "../i18n/index.js";

export function isRecognitionSupported() {
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
}

export function createRecognizer({ language, onResult, onError, onEnd }) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recognizer = new SpeechRecognition();
  recognizer.lang = voiceLang(language);
  recognizer.continuous = false;
  recognizer.interimResults = false;
  recognizer.maxAlternatives = 1;

  recognizer.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript ?? "";
    onResult(transcript.trim());
  };
  recognizer.onerror = (event) => onError(event.error ?? "unknown");
  recognizer.onend = () => onEnd();

  return recognizer;
}
