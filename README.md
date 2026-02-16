# Long-Form TTS Pipeline

Convert long texts into high-quality MP3 audio using [n8n](https://n8n.io) and [ElevenLabs](https://elevenlabs.io) -- fully self-hosted, no code required after setup.

## How It Works

```
Paste Text --> Sanitize --> Smart Chunk --> TTS & Assemble --> output_final.mp3
```

The pipeline handles texts of any length. It strips markdown formatting and emojis, splits at paragraph or sentence boundaries (max 1,200 chars per chunk) to avoid mid-sentence cuts, calls ElevenLabs v3 sequentially for each chunk, and uses FFmpeg to merge the audio into a single, seamless MP3 with correct duration metadata.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Docker** | Docker Desktop or Docker Engine with Compose v2 |
| **ElevenLabs Account** | Free tier works for short texts; Creator plan or higher recommended for long-form |
| **ElevenLabs API Key** | From your [ElevenLabs profile](https://elevenlabs.io) > Profile Settings > API Keys |
| **ElevenLabs Voice ID** | From Voice Lab after creating or selecting a voice |

---

## Quick Start

### 1. Clone the Repository

```bash
git clone <repo-url>
cd elevenLabs-n8n
```

### 2. Configure Credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your ElevenLabs credentials:

```
ELEVENLABS_API_KEY=sk_your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
```

**Where to find these:**

- **API Key** -- [elevenlabs.io](https://elevenlabs.io) > profile icon (top-right) > **Profile + API key** > copy.
- **Voice ID** -- **Voice Lab** > click the voice you want > Voice ID is on the voice card or in the URL.

### 3. Build and Start

```bash
docker compose up -d --build
```

First build takes ~30 seconds (downloads FFmpeg). Subsequent starts are instant. Wait ~10 seconds for n8n to initialize.

### 4. Create Your n8n Account

Open [http://localhost:5678](http://localhost:5678). On first launch, n8n asks you to create an owner account. Complete the setup wizard.

### 5. Import the Workflow

**Option A -- via the UI:**

1. Click **Add workflow** in the n8n dashboard.
2. Click the **...** menu (top-right of the editor).
3. Select **Import from File**.
4. Choose `workflows/longform_tts.json` from this project.

**Option B -- via command line:**

```bash
docker cp workflows/longform_tts.json n8n:/tmp/longform_tts.json
docker exec n8n n8n import:workflow --input=/tmp/longform_tts.json
```

You should see 5 connected nodes in a left-to-right chain.

### 6. Run It

1. Open the **Long-Form TTS Pipeline** workflow.
2. Double-click the **Set Input Text** node.
3. Replace the sample text with your content.
4. Close the node editor.
5. Click **Test Workflow** (play button at the bottom).
6. Wait for all nodes to turn green.

### 7. Get Your Audio

```bash
docker cp n8n:/home/node/.n8n/output_final.mp3 ./output_final.mp3
```

Play with any audio player or share directly (WhatsApp, Telegram, etc. -- duration displays correctly).

---

## Detailed Usage

### Preparing Your Text

Paste text from anywhere -- markdown editors, Google Docs, note-taking apps. The pipeline automatically strips:

- Markdown bold (`**text**`), italic (`_text_`), headings (`## text`)
- Strikethrough (`~~text~~`), links (`[text](url)`)
- Emojis
- Excess blank lines

Plain text with proper punctuation produces the best results.

### How Chunking Works

Text is split using a smart priority system (max 1,200 characters per chunk):

1. **Paragraph breaks** (`\n\n`) -- preferred, as they represent natural content boundaries
2. **Sentence boundaries** (`. `, `? `, `! `) -- used if no paragraph break is found
3. **Any whitespace** -- last resort to prevent mid-word cuts

Shorter chunks produce more natural-sounding audio with fewer artifacts at boundaries.

### Performance Expectations

| Input Size | Chunks | Approx. Time | Output Size |
|------------|--------|---------------|-------------|
| ~100 words (550 chars) | 1 | ~8 seconds | ~0.5 MB |
| ~500 words (3,000 chars) | 3 | ~25 seconds | ~3 MB |
| ~1,400 words (7,750 chars) | 7 | ~50 seconds | ~7 MB |
| ~5,000 words (27,500 chars) | 23 | ~3 minutes | ~25 MB |

Rule of thumb: ~1 MB of MP3 per minute of audio at 192 kbps.

---

## Workflow Nodes

| # | Node | Type | Purpose |
|---|------|------|---------|
| 1 | Manual Trigger | `manualTrigger` | Starts the workflow on demand |
| 2 | Set Input Text | `set` | Holds the text you paste in |
| 3 | Sanitize Text | `code` | Strips markdown, emojis, normalizes whitespace |
| 4 | Chunk Text | `code` | Splits text at paragraph/sentence boundaries (max 1,200 chars) |
| 5 | TTS & Assemble | `code` | Calls ElevenLabs API sequentially per chunk, saves each as a separate file, merges with FFmpeg (`-c:a libmp3lame`), returns the final MP3 |

The **TTS & Assemble** node handles everything in one place:
- Calls ElevenLabs for each chunk **one at a time, in order** (no parallel requests)
- Saves each response as a separate `.mp3` file
- Uses FFmpeg's **concat demuxer** with re-encoding to produce a seamless, single MP3 with correct duration metadata
- Includes retry logic (3 attempts, 5-second backoff) and rate-limit delays (500ms between chunks)
- Cleans up temporary files after merge

---

## Voice Configuration

### Choosing a Voice

1. Log in at [elevenlabs.io](https://elevenlabs.io).
2. Go to **Voice Lab** > **Add Generative or Cloned Voice** > **Voice Design**.
3. Describe the voice you want, for example:
   > Warm narrator, clear enunciation, calm and steady pace, professional tone.
4. Generate and preview samples until you find the right tone.
5. Save the voice.
6. Copy the **Voice ID** into your `.env` file.

### Switching Voices

1. Find the new Voice ID in ElevenLabs Voice Lab.
2. Update `ELEVENLABS_VOICE_ID` in `.env`.
3. Restart (plain `restart` does **not** reload `.env`):

   ```bash
   docker compose down && docker compose up -d --build
   ```

4. Verify the new value:

   ```bash
   docker exec n8n sh -c 'echo ${ELEVENLABS_VOICE_ID}'
   ```

### Voice Settings (ElevenLabs v3)

Configured inside the **TTS & Assemble** node's code. The v3 model uses **discrete** stability values:

| Parameter | Allowed Values | Default | Description |
|-----------|---------------|---------|-------------|
| `stability` | `0.0`, `0.5`, `1.0` | `0.5` | `0.0` = Creative, `0.5` = Natural, `1.0` = Robust |
| `similarity_boost` | 0.0 -- 1.0 | `0.80` | Higher = closer to the original voice |
| `style` | 0.0 -- 1.0 | `0.0` | Keep at 0.0 for neutral delivery |

To change: open the **TTS & Assemble** node and edit the `voice_settings` object in the code.

### Switching TTS Models

The workflow defaults to `eleven_v3`. To use a different model (e.g., `eleven_multilingual_v2`):

1. Open the **TTS & Assemble** node.
2. Change `model_id: 'eleven_v3'` to your desired model.
3. If using v2, note that `stability` accepts a continuous range (0.0--1.0) instead of discrete values.

---

## Managing the Service

| Action | Command |
|--------|---------|
| **Start** | `docker compose up -d --build` |
| **Stop** (keep data) | `docker compose down` |
| **Stop + delete all data** | `docker compose down -v` |
| **Restart after `.env` change** | `docker compose down && docker compose up -d --build` |
| **View logs** | `docker compose logs -f n8n` |
| **Copy output file** | `docker cp n8n:/home/node/.n8n/output_final.mp3 ./output_final.mp3` |

> **Important:** `docker compose restart` does **not** reload `.env` changes. Always use `down` then `up`.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| ElevenLabs returns **401** | Invalid API key | Check `ELEVENLABS_API_KEY` in `.env`; restart with `down`/`up` |
| ElevenLabs returns **400** "Invalid TTD stability" | v3 requires discrete stability values | Set `stability` to `0.0`, `0.5`, or `1.0` |
| ElevenLabs returns **429** | Rate limited | Wait and retry; pipeline has built-in 3x retry with 5s backoff |
| "access to env vars denied" | n8n security setting | Ensure `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` in `docker-compose.yml` |
| "file is not writable" | File access restricted | Ensure `N8N_RESTRICT_FILE_ACCESS_TO` and `N8N_BLOCK_FILE_ACCESS_TO_N8N_FILES` are set in `docker-compose.yml` |
| Env vars unchanged after edit | `restart` doesn't reload `.env` | Use `docker compose down && docker compose up -d --build` |
| Port 5678 already in use | Another service on that port | Stop the other service or change the port in `docker-compose.yml` |
| "Input text is empty or too short" | Text blank or under 10 chars | Paste actual content into **Set Input Text** |
| Audio jumps between chunks | Chunks too long or bad split point | Reduce `MAX_CHARS` in the Chunk Text node (default: 1200) |
| MP3 shows wrong duration | Old workflow version without FFmpeg merge | Re-import the latest `longform_tts.json` |

---

## Project Structure

```
elevenLabs-n8n/
  README.md                   # This guide
  Dockerfile                  # Extends n8n with static FFmpeg binary
  docker-compose.yml          # Container config (builds from Dockerfile)
  .env.example                # Credential template (safe to commit)
  .env                        # Your actual credentials (gitignored)
  .gitignore                  # Ignores .env, .mp3, temp data
  workflows/
    longform_tts.json         # Importable n8n workflow (5 nodes)
```

---

## How It Works Under the Hood

1. **Sanitize** -- Regex strips markdown formatting, emojis, and normalizes whitespace.
2. **Chunk** -- Splits text at paragraph breaks first, then sentence boundaries, never mid-word. Max 1,200 chars per chunk.
3. **TTS & Assemble** -- For each chunk (in order):
   - Calls `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` with the chunk text
   - Saves the MP3 response to a temp file (`tts_chunk_NNNN.mp3`)
   - Waits 500ms before the next call (rate limiting)
4. **FFmpeg Merge** -- Uses `ffmpeg -f concat -c:a libmp3lame -b:a 192k` to re-encode and merge all chunks into a single MP3 with seamless audio and correct duration.
5. **Cleanup** -- Removes temporary chunk files and the concat list.

---

## Security Notes

- `.env` is in `.gitignore` and will **never** be committed. API key and Voice ID stay local.
- The workflow reads credentials from environment variables at runtime -- nothing sensitive is stored in the JSON.
- n8n data (accounts, execution history) lives in a Docker volume (`n8n_data`) and persists across restarts.
- To fully reset, run `docker compose down -v`.

---

## License

MIT
