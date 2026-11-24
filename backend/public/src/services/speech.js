// Browser text-to-speech. When an AI answer is available, it is spoken with a
// device voice matching the selected language (en-IN, te-IN, hi-IN, ta-IN,
// mr-IN). If that exact voice is missing, the browser still gets the language
// tag and uses the closest installed voice.

import { voiceLang } from "../i18n/index.js";

function findVoice(lang) {
  if (!("speechSynthesis" in window)) return null;
  const voices = window.speechSynthesis.getVoices() ?? [];
  return (
    voices.find((voice) => voice.lang.toLowerCase() === lang.toLowerCase()) ??
    voices.find((voice) => voice.lang.toLowerCase().startsWith(lang.slice(0, 2).toLowerCase())) ??
    null
  );
}

export function speak(text, language) {
  if (!("speechSynthesis" in window) || !text) {
    return false;
  }

  window.speechSynthesis.cancel();

  const lang = voiceLang(language);
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang;
  utterance.rate = 0.9;

  const voice = findVoice(lang);
  if (voice) utterance.voice = voice;

  window.speechSynthesis.speak(utterance);
  return true;
}

export function stopSpeaking() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}
