---
name: n8n-workflow-expert
description: Expert in building n8n workflows, handling binary data, and writing JavaScript for Code nodes. Includes text sanitization, sentence-aware chunking, and MP3 binary concatenation. Use when the user asks about n8n workflow creation, Code node logic, binary data merging, text chunking, or workflow JSON export/import.
---

# n8n Workflow Expert

## Role

Advanced n8n automation agent specializing in Node.js-based data transformation and binary stream management.

## Core Competencies

### 1. Workflow Architecture

- Building JSON-based workflows with standard nodes: `manualTrigger`, `httpRequest`, `code`, `writeBinaryFile`.
- Using n8n expressions: `{{ $json.field }}`, `{{ $input.item.json }}`, and `{{ $env.VAR }}`.
- Managing execution modes: distinguish between "Run once for all items" and "Run once for each item."
- Exporting workflows as JSON via Settings > Export and importing via Settings > Import from File.

### 2. Text Processing (Phase 2)

Implement sanitization regex to strip Markdown and normalize input:

```javascript
function sanitize(input) {
  return input
    .replace(/\*\*/g, "")           // bold
    .replace(/#{1,6}\s?/g, "")      // headings
    .replace(/~~.*?~~/g, "")        // strikethrough
    .replace(/_([^_]+)_/g, "$1")    // italic
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // links
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}]/gu, "")
    .replace(/\n\s*\n/g, "\n\n")
    .trim();
}
```

Implement sentence-aware chunking: find the last `.`, `!`, or `?` before the 2500-character limit to prevent mid-sentence breaks.

```javascript
const MAX_CHARS = 2500;
let slice = remainingText.substring(0, MAX_CHARS);
let lastIndex = Math.max(
  slice.lastIndexOf('. '),
  slice.lastIndexOf('? '),
  slice.lastIndexOf('! ')
);
if (lastIndex === -1) lastIndex = slice.lastIndexOf(' ');
if (lastIndex === -1) lastIndex = MAX_CHARS; // force-split fallback
```

### 3. Binary and Audio Assembly (Phase 4)

- Use `helpers.getBinaryDataBuffer(index, propertyName)` to retrieve raw audio chunks.
- Use `Buffer.concat([buffers])` to merge MP3 streams.
- Use `helpers.prepareBinaryData(buffer, fileName, mimeType)` to output the final merged file.

```javascript
const items = $input.all();
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
    size_mb: (mergedBuffer.length / (1024 * 1024)).toFixed(2),
    chunks_merged: items.length
  },
  binary: {
    data: await this.helpers.prepareBinaryData(
      mergedBuffer, 'meditation_final.mp3', 'audio/mpeg'
    )
  }
};
```

**Important:** The binary merge node must execute in "Run once for all items" mode to collect every chunk before concatenation.

## Quality Standards

- **Error Handling:** Always wrap Code node logic in try-catch blocks.
- **Memory Management:** Ensure chunks are sorted by `chunk_index` before concatenation to maintain audio chronology.
- **Input Validation:** Guard against empty or too-short input before processing.

```javascript
if (!text || text.length < 10) {
  throw new Error("Input text is empty or too short for TTS generation");
}
```

## Workflow JSON Structure

When building exportable workflow JSON, each node requires:
- `id`: unique string
- `name`: display name
- `type`: full node type (e.g., `n8n-nodes-base.code`)
- `position`: `[x, y]` coordinates
- `parameters`: node-specific config
- `typeVersion`: match the n8n version in use

Connections are defined separately in a `connections` object mapping source node outputs to target node inputs.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Expression returns undefined | Wrong path to field | Check `$json` vs `$input.item.json` |
| Binary data missing | Wrong property name | Verify `data` matches the HTTP response key |
| Chunks out of order | Missing sort | Add `.sort((a,b) => a.json.chunk_index - b.json.chunk_index)` |
| Code node timeout | Large payload | Increase node timeout or reduce chunk size |
