# Reading book pages (local multimodal)

How Bookworm turns **page photos** (or markdown stand-ins) into **study notes** the agent can practice from — **without paid API keys**.

```
phone photo / screenshot
        │
        ▼
 bookworm ingest-pages
   ├── --backend mock     → sidecar .md/.txt (offline)
   └── --backend ollama   → local vision model (free)
        │
        ▼
 data/domains/<domain>/pages/
   ├── images/<id>.png
   ├── <id>.md
   └── pages.json  (updated)
        │
        ▼
 bookworm run [--vision mock|ollama]
        │
        ▼
 study notes → practice → skill heatmap
```

---

## Quick start

### Offline mock (no vision model)

Uses a text sidecar next to each image: `demo_fbd.png` + `demo_fbd.md`.

```bash
bookworm ingest-pages examples/sample_page_photo --backend mock --skills free_body
```

### Local multimodal LLM (Ollama)

```bash
# one-time free download
ollama pull moondream

bookworm doctor   # expect: ollama vision ✓

bookworm ingest-pages ./my_photos \
  --backend ollama \
  --domain mechanics_demo \
  --skills free_body,newtons_2nd \
  --hint "intro classical mechanics"
```

### During a learning session

If a page in the domain has a real `image_path`, you can re-read it with vision in the study phase:

```bash
bookworm run --vision mock     # sidecars / offline
bookworm run --vision ollama   # local VLM
bookworm run                   # text/markdown only (default)
```

Default `bookworm run` does **not** call vision — it uses existing page text. That keeps demos fast and deterministic.

---

## CLI reference: `bookworm ingest-pages`

```text
bookworm ingest-pages SOURCE [OPTIONS]
```

| Argument / option | Description |
|-------------------|-------------|
| `SOURCE` | Image file **or** folder of images |
| `-d, --domain` | Domain folder under `data/domains/` (default: `mechanics_demo`) |
| `-b, --backend` | `mock` (default) or `ollama` |
| `-s, --skills` | Comma-separated skill ids to tag, e.g. `free_body,newtons_2nd` |
| `--model` | Ollama vision model override |
| `--hint` | Extra context for the VLM (topic, chapter, course) |
| `--dry-run` | Print notes; do not write files |
| `--no-copy` | Do not copy images into the domain `pages/images/` folder |

**Supported image types:** `.png` `.jpg` `.jpeg` `.webp` `.gif` `.bmp`

### Examples

```bash
# Single photo
bookworm ingest-pages ~/Pictures/textbook_p42.jpg --backend ollama -s free_body

# Folder of pages
bookworm ingest-pages ./photos --backend ollama -d mechanics_demo

# Preview without writing
bookworm ingest-pages ./photos --backend mock --dry-run

# Custom vision model
bookworm ingest-pages ./photos --backend ollama --model llava
```

---

## Backends

### `mock` (default)

| | |
|--|--|
| **Needs** | Nothing (no Ollama) |
| **How it works** | For `page.png`, looks for `page.md` or `page.txt` beside it |
| **Best for** | CI, demos, authoring, machines without a GPU |
| **Fallback** | If no sidecar, writes a stub note telling you to add one |

Sidecar tip: include the same hints the mock student understands:

```markdown
# Free-body diagrams

- Isolate one body
- Draw external forces only

PROBE_HINT: fbd_what => all external forces on an isolated body
ANSWER_KEY: free_body => isolate body; external forces only
```

### `ollama` (local VLM)

| | |
|--|--|
| **Needs** | [Ollama](https://ollama.com) + a **vision** model |
| **How it works** | Sends the image (base64) to Ollama `/api/chat` with a JSON study prompt |
| **Best for** | Real textbook photos, diagrams, “looks like reading” demos |
| **Cost** | $0 (your electricity / GPU/CPU time) |

#### Recommended vision models

| Model | Notes |
|-------|--------|
| `moondream` | Small, good default for stingy machines |
| `llava` | Common, larger |
| `minicpm-v` | Strong small VLM option |
| `llama3.2-vision` | Meta vision variant |

```bash
ollama pull moondream
# optional:
set BOOKWORM_OLLAMA_VISION_MODEL=moondream          # Windows PowerShell: $env:BOOKWORM_OLLAMA_VISION_MODEL="moondream"
export BOOKWORM_OLLAMA_VISION_MODEL=moondream       # macOS/Linux
```

Related env vars (see also [LOCAL_STACK.md](LOCAL_STACK.md)):

| Variable | Purpose | Default |
|----------|---------|---------|
| `BOOKWORM_OLLAMA_HOST` | Ollama base URL | `http://127.0.0.1:11434` |
| `BOOKWORM_OLLAMA_MODEL` | Text student model | auto-pick small installed model |
| `BOOKWORM_OLLAMA_VISION_MODEL` | Vision model for pages | auto-pick vision model if installed, else `moondream` |

`bookworm doctor` reports whether text and vision models are reachable.

---

## What gets written

For each image `newton_laws.png` ingested into domain `mechanics_demo`:

```text
data/domains/mechanics_demo/pages/
├── images/
│   └── newton_laws.png      # copy of the photo (unless --no-copy)
├── newton_laws.md           # study notes as markdown
└── pages.json               # index entry created or updated
```

### `pages.json` entry (shape)

```json
{
  "id": "newton_laws",
  "title": "Newton's second law",
  "skill_ids": ["newtons_2nd"],
  "book_refs": ["newton_laws"],
  "image_path": "images/newton_laws.png",
  "text": "",
  "key_ideas": ["..."],
  "formulas": ["F = ma"]
}
```

- `text` is often left empty in JSON; the loader fills it from `<id>.md`.
- `image_path` is resolved relative to the `pages/` directory when the domain loads.
- Re-ingesting the same page id **updates** the existing entry.

### Study note fields (from the VLM)

The vision prompt asks for JSON:

| Field | Meaning |
|-------|---------|
| `title` | Short page title |
| `summary` | 2–4 sentence summary |
| `key_ideas` | Bullet list of concepts |
| `formulas` | Equations seen on the page |
| `raw_text` | Transcript / readable text |
| `skill_ids` | Optional tags (seeded by `--skills`) |

If the model returns non-JSON, Bookworm still saves a note using the raw text as summary/transcript.

---

## How reading plugs into the learning loop

```
probe → diagnose gaps → study plan → [read pages] → practice → evaluate
```

1. **Study plan** maps gap skills → `book_refs` / page ids (`skills.yaml` + library).
2. **`run_study`** loads those pages:
   - **No `--vision`:** use markdown/text (`extract_study_note`).
   - **`--vision mock|ollama`:** if `image_path` exists on disk, call the vision/mock reader; else fall back to text.
3. **Student** ingests study notes (mock student picks up `PROBE_HINT` lines; Ollama student gets notes in context).
4. **Practice / eval** are unchanged — still graded outside the student.

### Student backend vs vision backend

These are independent:

| Flag | Controls |
|------|----------|
| `--backend mock\|ollama` | Who **answers probes** (the student) |
| `--vision mock\|ollama` | How **pages with images** are read during study |
| `ingest-pages --backend` | How **photos are turned into domain pages** up front |

Example: ingest with vision once, then run with a cheap mock student:

```bash
bookworm ingest-pages ./photos --backend ollama -s free_body
bookworm run --backend mock
```

---

## Authoring pages without photos

You can still write textbooks by hand (best quality control):

1. Add `pages/my_page.md`
2. Register in `pages/pages.json` with `skill_ids` and `book_refs`
3. Link from `skills.yaml` via `book_refs: [my_page]`

See `data/domains/mechanics_demo/` for a full example.

---

## Sample assets

| Path | Purpose |
|------|---------|
| `examples/sample_page_photo/demo_fbd.png` | Tiny placeholder image |
| `examples/sample_page_photo/demo_fbd.md` | Sidecar for mock vision |
| `examples/sample_page_photo/README.md` | Short usage note |

Replace the PNG with a real page photo anytime; keep or delete the sidecar depending on backend.

---

## Code map

| Module | Role |
|--------|------|
| `src/bookworm/agents/ollama.py` | Ollama HTTP client: text `chat`, multimodal `chat_vision`, model pickers |
| `src/bookworm/reading/vlm.py` | Mock + Ollama page readers; JSON parse; markdown export |
| `src/bookworm/reading/ingest.py` | Folder walk, domain write, image copy |
| `src/bookworm/reading/page_ingest.py` | `Page` / `PageLibrary`; study helpers |
| `src/bookworm/core/study.py` | Study phase wiring (`vision_backend`) |
| `src/bookworm/cli.py` | `ingest-pages`, `run --vision`, `doctor` |

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| `Vision backend unavailable` | `ollama pull moondream`; re-run `bookworm doctor` |
| Ollama up but “no vision model” | Text-only models (`smollm2`, tiny `gemma3`) don’t count; pull a vision tag |
| Empty / garbage notes | Use a larger VLM; add `--hint`; improve photo lighting/crop |
| Mock notes say “No sidecar” | Add `same_name.md` next to the image |
| Domain didn’t update | Drop `--dry-run`; check `data/domains/<domain>/pages/` |
| `run --vision` does nothing special | Pages need a valid `image_path` file on disk |
| Slow ingest | Expected on CPU; use `moondream` or fewer pages |

---

## Design notes

1. **Grade outside the reader** — vision extracts notes; probes still use answer keys / judges.  
2. **Mock path is first-class** — CI and stingy machines never depend on a VLM.  
3. **Books before web** — ingest is for *your* pages, not scrape-the-internet.  
4. **Copyright** — personal study of books you own is the intended use; don’t publish fine-tunes of others’ textbooks without rights.  
5. **Robots later** — Reachy Mini / desk camera can dump frames into the same `ingest-pages` folder.

---

## Related docs

- [LOCAL_STACK.md](LOCAL_STACK.md) — $0 stack and Ollama setup  
- [DEMO.md](DEMO.md) — talk tracks and demo script  
- [../ROADMAP.md](../ROADMAP.md) — phases (reading is Phase 1)  
