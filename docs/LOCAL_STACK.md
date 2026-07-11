# Local / free stack (no paid API keys)

Bookworm Bot is designed to be **stingy-friendly**. Default path costs **$0**.

## What works today with zero keys

```bash
pip install -e ".[dev]"
bookworm run                 # mock student
bookworm run -m exploratory  # still free
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
| **0 – Mock** | $0 | Full loop, deterministic demos | default |
| **1 – Ollama** | $0 (your GPU/CPU) | Real LLM answers from local model | `bookworm run --backend ollama` |
| **2 – Local OCR** | $0 | Text from page photos | Tesseract / EasyOCR (Phase 1) |
| **3 – Local VLM** | $0 | Diagrams + layout from photos | Ollama vision models (Phase 1+) |
| **4 – Local LoRA** | $0 (electricity) | Adapter FT on your machine | Unsloth / PEFT later |

Paid APIs are **optional convenience**, never required.

---

## Ollama (recommended free “real student”)

1. Install [Ollama](https://ollama.com/) (free, local).
2. Pull a small model, e.g.:

   ```bash
   ollama pull llama3.2
   # or smaller: ollama pull qwen2.5:0.5b
   ```

3. Run Bookworm against it:

   ```bash
   bookworm doctor              # checks mock + ollama reachability
   bookworm run --backend ollama
   # optional:
   set BOOKWORM_OLLAMA_MODEL=llama3.2
   set BOOKWORM_OLLAMA_HOST=http://127.0.0.1:11434
   ```

If Ollama is down, the CLI fails clearly (or use `--backend mock`).

No account. No credit card. Models stay on disk.

---

## Page photos without cloud vision

Phase 1 preference order:

1. **Hand-typed / markdown pages** (already supported) — best quality/$  
2. **Tesseract OCR** on phone photos — free, offline  
3. **Ollama vision** (`llava`, `moondream`, etc.) — free, offline, better on diagrams  
4. Cloud VLMs — only if you later want convenience  

---

## Fine-tuning without a lab budget

When we get there:

- Prefer **memory / notes** over weight updates  
- If FT: small **LoRA** on a 1–3B local model, only if held-out probes improve  
- Export datasets from sessions (JSONL) so training can happen on a free Colab GPU *if you choose* — still optional  

---

## What we will not default to

- Required OpenAI/Anthropic keys for CI or demos  
- “Just scrape the web and fine-tune” as the main path  
- Heavy cloud GPU for the happy path  

Cloud remains a *power-user* backend if someone else brings keys.
