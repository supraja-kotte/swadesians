# Natural-language voice assistant

The assistant now has two modes:

1. **Fixed commands (always available, no key)** — navigation, read-aloud and
   help. Speech recognition and text-to-speech use the device's own browser
   engine; audio is not uploaded.
2. **Natural-language answers (enabled by a server-side key)** — the farmer can
   ask any farming question by voice or by typing. The backend calls an AI
   provider and returns plain prose in the selected language. The answer is
   then read aloud with a device voice matching that language.

There is **no AI key in the frontend**. The browser only sees
`GET /api/assistant/config`, which reports `available: true/false`.

## Setup

Copy `backend/.env.example` to `backend/.env` and set:

```dotenv
AI_PROVIDER=openai          # or: gemini
AI_API_KEY=your-key-here
AI_MODEL=                   # optional; sensible default per provider
AI_BASE_URL=https://api.openai.com/v1   # only for OpenAI-compatible services
```

Then restart the backend. The assistant page will switch to question mode
automatically. With no key it keeps the honest fixed-command behaviour.

### Providers

- `openai` — calls `{AI_BASE_URL}/chat/completions`. Works with OpenAI and
  compatible gateways that accept the same request shape.
- `gemini` — calls Gemini `generateContent` and sends the key in the
  `x-goog-api-key` header, not in the URL.

Both use Python's standard library; no new runtime dependency was added.

## Language behaviour

The five supported languages are English, Telugu, Hindi, Tamil and Marathi.
The system prompt asks the model to answer in natural spoken language, with
short sentences, and explicitly forbids command IDs, codes, JSON, binary
notation and technical symbols. It also forbids invented prices, sellers,
scheme names, benefit amounts and guaranteed yields, and asks the farmer to
confirm important decisions with an official source or local office.

Text-to-speech selects an installed voice for `en-IN`, `te-IN`, `hi-IN`,
`ta-IN` or `mr-IN`. If the exact voice is not installed, the browser uses the
closest available voice for that language. Voice quality therefore depends on
the device; a provider-hosted TTS voice can be added later if needed.

## Safety and limits

- `POST /api/assistant/ask` validates a 2–500 character question and a supported
  language code.
- A small in-process limit allows 20 questions per client per 60 seconds
  (`429` after that). Multiple workers need a shared store.
- Provider failures return `502`; a missing key returns `503`. The browser
  shows a translated error rather than inventing an answer.
- Answers are not stored in the database. Only the question text is sent to
  the configured provider.
- Review the provider's data-retention terms before using real farmer data.

## Tests

`tests/test_ai_assistant.py` checks the keyless fallback, prompt language,
plain-prose cleaning, validation and rate limiting with a mocked provider.
No real key is needed to run the suite.
