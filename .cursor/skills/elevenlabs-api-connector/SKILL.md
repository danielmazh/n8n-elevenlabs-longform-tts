---
name: elevenlabs-api-connector
description: Manages integration with ElevenLabs REST API for text-to-speech. Handles authentication, endpoint schema, voice settings, model selection, and rate limits. Use when working with ElevenLabs TTS, voice generation, audio synthesis, or speech API calls.
---

# ElevenLabs API Connector

## Role

Technical interface for ElevenLabs Speech Synthesis integration.

## API Specifications

### 1. Request Structure

- **Endpoint:** `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`
- **Headers:**
  - `xi-api-key`: User-provided API Key.
  - `Content-Type`: `application/json`.
- **Model ID:** Default to `eleven_multilingual_v2` for high-quality, nuanced output.

**Request body:**

```json
{
  "text": "The meditation text to synthesize.",
  "model_id": "eleven_multilingual_v2",
  "voice_settings": {
    "stability": 0.65,
    "similarity_boost": 0.80,
    "style": 0.0
  }
}
```

### 2. Voice Settings (Meditation Optimized)

| Parameter | Range | Recommended | Purpose |
|-----------|-------|-------------|---------|
| `stability` | 0.0 - 1.0 | 0.60 - 0.75 | Higher for consistent meditation tones |
| `similarity_boost` | 0.0 - 1.0 | 0.75 - 0.85 | Clarity enhancement |
| `style` | 0.0 - 1.0 | 0.0 | Neutral delivery for affirmations |

**Voice design prompt:** "Mature male, deep resonant tone, slow rhythmic delivery, authoritative and empathetic mentor style, clear and deliberate."

### 3. Response Format

- **Content-Type:** `audio/mpeg`
- **Format:** Raw binary MP3 stream
- **Response is streamed** -- in n8n, set HTTP Response Format to "File" to capture as binary

### 4. Available Models

| Model | Use Case |
|-------|----------|
| `eleven_multilingual_v2` | Default. Best quality, supports 29 languages |
| `eleven_monolingual_v1` | English-only, faster, lower latency |
| `eleven_turbo_v2_5` | Lowest latency, slightly lower quality |

### 5. Rate Limits and Quotas

- **Creator plan:** ~100 requests/min
- Implement 1-second delay between chunk requests in n8n
- Monitor for `429 Too Many Requests` -- back off and retry
- **Character limit per request:** 5,000 max (use 2,500 for stability)
- Monthly character quota depends on plan tier

## Authentication

API key is retrieved from ElevenLabs dashboard: Profile Settings > API Keys.

In n8n, inject via environment variable:

```
# .env
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
```

Reference in HTTP Request node headers: `{{ $env.ELEVENLABS_API_KEY }}`

## Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| `401` | Unauthorized | Verify `xi-api-key` header value matches dashboard key |
| `400` | Bad Request | Validate JSON body structure, especially nested `voice_settings` |
| `422` | Validation Error | Text is empty or exceeds character limit |
| `429` | Rate Limited | Add delay between requests, check quota usage |
| `500` | Server Error | Retry with exponential backoff (3 attempts, 5s interval) |

## n8n HTTP Request Node Config

```
Method: POST
URL: https://api.elevenlabs.io/v1/text-to-speech/{{ $env.ELEVENLABS_VOICE_ID }}
Authentication: None (key in header)
Headers:
  xi-api-key: {{ $env.ELEVENLABS_API_KEY }}
  Content-Type: application/json
Body Content Type: JSON
Response Format: File
Retry on Fail: Yes
Max Tries: 3
Wait Between Tries: 5000ms
```

## Voice Creation Workflow

1. Log in at https://elevenlabs.io
2. Navigate to Voice Lab
3. Click "Add Generative or Cloned Voice" > Voice Design
4. Enter the meditation voice prompt (see section 2)
5. Generate and preview multiple samples
6. Save the voice and copy the Voice ID from the voice card
7. Store as `ELEVENLABS_VOICE_ID` in `.env`
