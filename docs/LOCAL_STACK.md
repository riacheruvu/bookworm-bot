# Local / free stack (no paid API keys)

Bookworm Bot is designed to be **stingy-friendly**. Default path costs **$0**.

For **page photos and multimodal reading**, see the full guide: **[READING.md](READING.md)**.

## What works today with zero keys

```bash
pip install -e ".[dev]"
bookworm doctor              # mock + optional Ollama checks
bookworm run                 # mock student
bookworm run -m exploratory  # still free
bookworm ingest-pages examples/sample_page_photo --backend mock
pytest                       # free
```

The mock student is intentionally weak until it “reads” pages, then improves via
hints absorbed from local textbook files. That is enough to:

- develop the learning loop
- author domains / probes / pages
- measure pre/post accuracy
- hack skill graphs and study plans

**You do not need OpenAI, Anthropic, or any cloud bill to contribute.**

---

## Free upgrade ladder

| Tier | Cost | What you get | How |
|------|------|--------------|-----|
| **0 – Mock student** | $0 | Full loop, deterministic demos | `bookworm run` (default) |
| **1 – Ollama text** | $0 (your GPU/CPU) | Real LLM answers | `bookworm run --backend ollama` |
| **2 – Mock vision** | $0 | Photos + sidecar `.md` | `ingest-pages --backend mock` |
| **3 – Ollama vision** | $0 | Local multimodal page reading | `ingest-pages --backend ollama` |
| **4 – Local LoRA** | $0 (electricity) | Adapter FT on your machine | later (Unsloth / PEFT) |

Paid APIs are **optional convenience**, never required.

---

## Ollama (text student)

1. Install [Ollama](https://ollama.com/) (free, local).
2. Pull a small **text** model:

   ```bash
   ollama pull smollm2:360m
   # or: ollama pull qwen2.5:0.5b / llama3.2
   ```

3. Run:

   ```bash
   bookworm doctor
   bookworm run --backend ollama
   ```

### Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `BOOKWORM_OLLAMA_HOST` | Ollama URL | `http://127.0.0.1:11434` |
| `BOOKWORM_OLLAMA_MODEL` | Text student | auto-pick small installed model |
| `BOOKWORM_OLLAMA_VISION_MODEL` | Page VLM | auto-pick vision model / `moondream` |

```bash
# Windows PowerShell
$env:BOOKWORM_OLLAMA_MODEL = "qwen3:0.6b"
$env:BOOKWORM_OLLAMA_VISION_MODEL = "moondream"

# macOS / Linux
export BOOKWORM_OLLAMA_MODEL=qwen3:0.6b
export BOOKWORM_OLLAMA_VISION_MODEL=moondream
```

---

## Ollama (vision / page photos)

```bash
ollama pull moondream
bookworm doctor   # ollama vision ✓
bookworm ingest-pages ./photos --backend ollama --skills free_body
bookworm run --vision ollama
```

Details, file layout, and troubleshooting: **[READING.md](READING.md)**.

---

## Fine-tuning without a lab budget

When we get there:

- Prefer **memory / notes** over weight updates  
- If FT: small **LoRA** on a 1–3B local model, only if held-out probes improve  
- Export datasets from sessions (JSONL) — free Colab GPU optional, never required  

---

## What we will not default to

- Required OpenAI/Anthropic keys for CI or demos  
- “Just scrape the web and fine-tune” as the main path  
- Heavy cloud GPU for the happy path  

Cloud remains a *power-user* backend if someone else brings keys.
