# Long-Form Meditation TTS Implementation Plan

---

## Phase 1: Infrastructure and Environment Setup

### 1.1 Deploy n8n via Docker

Run n8n in a containerized environment to manage binary data and persistence.

**Command:**

```bash
docker run -d --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -e N8N_LOG_LEVEL=info \
  -e N8N_METRICS=true \
  --restart always \
  n8nio/n8n

```

### 1.2 ElevenLabs Configuration

1. Log in to ElevenLabs.
2. Navigate to **Voice Lab** and create a new voice using the **Voice Design** tool.
3. Prompt for Voice: *Mature male, deep resonant tone, slow rhythmic delivery, authoritative and empathetic mentor style, clear and deliberate.*
4. Record the **Voice ID** from the voice card.
5. Retrieve your **API Key** from Profile Settings.

---

## Phase 2: Text Processing and Sanitization

### 2.1 The Sanitization Node

This node cleans the input text and prepares it for the TTS engine.

**JavaScript (n8n Code Node):**

```javascript
const text = $input.item.json.text || "";

function sanitize(input) {
  return input
    .replace(/\*\*/g, "")
    .replace(/#{1,6}\s?/g, "")
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}]/gu, "")
    .replace(/\n\s*\n/g, "\n\n")
    .trim();
}

return { json: { clean_text: sanitize(text) } };

```

### 2.2 The Sentence-Aware Chunking Node

Splits text into chunks of maximum 2500 characters, ensuring it does not break mid-sentence.

**JavaScript (n8n Code Node):**

```javascript
const fullText = $input.item.json.clean_text;
const MAX_CHARS = 2500;
const chunks = [];

let remainingText = fullText;

while (remainingText.length > 0) {
  if (remainingText.length <= MAX_CHARS) {
    chunks.push(remainingText);
    break;
  }

  let slice = remainingText.substring(0, MAX_CHARS);
  let lastIndex = Math.max(
    slice.lastIndexOf('. '),
    slice.lastIndexOf('? '),
    slice.lastIndexOf('! ')
  );

  if (lastIndex === -1) lastIndex = slice.lastIndexOf(' ');

  const finalSlice = remainingText.substring(0, lastIndex + 1).trim();
  chunks.push(finalSlice);
  remainingText = remainingText.substring(lastIndex + 1).trim();
}

return chunks.map((chunk, index) => ({
  json: { chunk_text: chunk, chunk_index: index, total_chunks: chunks.length }
}));

```

---

## Phase 3: TTS API Orchestration

### 3.1 HTTP Request Configuration

Configure the HTTP Request node to call the ElevenLabs API.

* **Method:** POST
* **URL:** `https://api.elevenlabs.io/v1/text-to-speech/{{VOICE_ID}}`
* **Headers:**
* `xi-api-key`: `{{YOUR_API_KEY}}`
* `Content-Type`: `application/json`


* **Body Parameters:**
* `text`: `{{ $json.chunk_text }}`
* `model_id`: `eleven_multilingual_v2`
* `voice_settings`:
* `stability`: 0.65
* `similarity_boost`: 0.80




* **Response Format:** File

---

## Phase 4: Binary Assembly

### 4.1 The Binary Merger Node

This node collects all incoming binary chunks, sorts them by index, and concatenates them into a single file.

**JavaScript (n8n Code Node):**

```javascript
const items = $input.all();
if (items.length === 0) return [];

// Sort by index to maintain chronology
items.sort((a, b) => a.json.chunk_index - b.json.chunk_index);

const buffers = [];
for (let i = 0; i < items.length; i++) {
  const buffer = await this.helpers.getBinaryDataBuffer(i, 'data');
  buffers.push(buffer);
}

const mergedBuffer = Buffer.concat(buffers);

return {
  json: {
    fileName: "meditation_final.mp3",
    size_mb: (mergedBuffer.length / (1024 * 1024)).toFixed(2)
  },
  binary: {
    data: await this.helpers.prepareBinaryData(mergedBuffer, 'meditation_final.mp3', 'audio/mpeg')
  }
};

```

---

## Phase 5: Error Handling and Scaling

1. **Retry Logic:** Set the HTTP Request node to retry on failure (3 attempts, 5-second interval) to handle network blips.
2. **Concurrency:** Set the loop execution to "Wait 1 second" between requests to stay within API rate limits for the Creator plan.
3. **Storage:** Add a final node (Google Drive or S3) to upload the `meditation_final.mp3` automatically.

---

## Phase 6: Testing Protocol

1. **Unit Test:** Run with a 100-word text to verify the full flow.
2. **Load Test:** Run with a 5000-word text to verify memory stability and chunking logic.
3. **Quality Audit:** Verify the transition between chunks is seamless without audible clicks or tone shifts.

---

**Confidence Level:** High

Would you like me to generate the raw JSON for the n8n workflow so you can import it directly?