# Bookworm Bot 📚🤖

[![GitHub](https://img.shields.io/badge/github-riacheruvu%2Fbookworm--bot-blue?logo=github)](https://github.com/riacheruvu/bookworm-bot)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Thesis:** Can an AI agent improve on a held-out skill suite by (1) failing probes, (2) selecting pages from a physical-style textbook (images/text mocks), (3) converting reading into practice, and (4) optionally adapting later (LoRA / memory) — without unrestricted web fine-tuning?

**Repo:** https://github.com/riacheruvu/bookworm-bot  
**Scope & phases:** see [ROADMAP.md](ROADMAP.md)

**Bookworm Bot** is a hackable scaffold for that loop:

```
probe → diagnose gaps → study book pages → practice → evaluate
```

Serious mode keeps grading strict. Exploratory / flexible modes let the agent invent probe variants and wander a bit — dial it up when you're exploring, dial it down when you're measuring learning.

---

## Quick start

```bash
cd bookworm-bot
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -e ".[dev]"
bookworm run
# or:
python -m bookworm run --mode exploratory
```

Useful commands:

```bash
bookworm domains
bookworm run -d mechanics_demo -m serious
bookworm run -m flexible --variants
bookworm show-session data/sessions/<id>.json
pytest
```

You should see a skill heatmap, study plan, and a rough **improved?** signal (practice accuracy vs probe accuracy).

---

## Why this exists

Most “AI that reads” demos are RAG over PDFs. This project treats **study as a skill**:

1. Attempt concrete probes  
2. Detect skill gaps from **behavior** (failures), not vibes  
3. Read **book-like pages** (mock physical books via text/images first)  
4. Practice what you read  
5. Measure whether you got better  

Web search / scrapers can plug in later as a fallback — **books first**.

Inspired in spirit by efficient adaptation + learning-by-doing research culture (e.g. Thinking Machines–style LoRA / on-policy ideas as a *later* phase), and embodiment paths like **Reachy Mini** for camera-based page intake — not required for v0.

---

## Repo layout

```
bookworm-bot/
├── src/bookworm/
│   ├── agents/          # StudentAgent (mock now; swap in LLMs later)
│   ├── core/            # probe, gaps, study, practice, eval, full loop
│   ├── models/          # Skill graph, probes, sessions
│   ├── reading/         # Page library / OCR-VLM mock
│   ├── envs/            # Phase 3 stubs (dynamic sims, Reachy Mini)
│   └── cli.py
├── data/domains/
│   └── mechanics_demo/  # skills + probes + mock textbook pages
├── data/sessions/       # saved run JSON (gitignored contents)
├── examples/
└── tests/
```

---

## Learning phases (roadmap)

| Phase | Goal | Status in repo |
|-------|------|----------------|
| **0 – Scaffold** | Runnable loop + demo domain | ✅ you are here |
| **1 – Real reading** | Page images → VLM/OCR → structured notes | hooks ready (`Page.image_path`) |
| **2 – Better students** | LLM backend, memory store, optional LoRA with eval gates | `StudentAgent.backend` |
| **3 – Dynamic envs** | Parametric sims from skill gaps | `src/bookworm/envs/` |
| **4 – Embodiment** | Reachy Mini camera + desk demos | docs stub |

---

## Probe modes

| Mode | Behavior |
|------|----------|
| `serious` | Fixed answer keys, objective grading (default for real progress) |
| `exploratory` | Soft/open probes; agent may invent variants; ungraded when no key |
| `flexible` | Mix of structured + open items |

Toggle on the CLI: `--mode serious|exploratory|flexible` and `--variants`.

---

## Demo domain: `mechanics_demo`

Tiny classical-mechanics curriculum:

- Skills: SI units → free-body diagrams → Newton’s 2nd → friction → work–energy  
- Probes: short answer / numeric with keys  
- Pages: markdown “textbook” pages with `PROBE_HINT` lines so the **mock student can actually improve after studying**

That’s intentional: v0 proves the *loop*, not intelligence.

### Add your own domain

Copy `data/domains/mechanics_demo/` → `data/domains/my_domain/`:

1. `skills.yaml` — skill graph + `book_refs`  
2. `probes.json` — probes with `skill_ids` + answer keys  
3. `pages/pages.json` + `pages/*.md` — book content (later: images)

Then:

```bash
bookworm run -d my_domain
```

---

## Hacking guide

### Swap in a real model

Edit / extend `src/bookworm/agents/student.py`:

- Add `backend="openai"` (or local llama.cpp, etc.)  
- Keep **grading outside** the student so it can’t mark its own homework  

### Real book photos

1. Drop images under `data/domains/<domain>/pages/`  
2. Set `image_path` in `pages.json`  
3. Replace `extract_study_note` with a VLM call that returns summary / formulas / skills  

### Fine-tuning later (not day one)

Only promote adapters when:

- You have clean `(prompt, reasoning, answer)` pairs  
- Held-out probe accuracy beats baseline  
- Prefer memory / RAG until that bar is clear  

### Dynamic envs + Reachy Mini

See `src/bookworm/envs/README.md`. Start with **parametric templates** (μ, mass, incline), not free-form world gen.

---

## Design principles

1. **Gaps from failures**, not self-report  
2. **Books before web** for deliberate study  
3. **Measure learning** (pre/post probes) every session  
4. **Mock embodiment early**; robots later  
5. **FT is a privilege** earned by eval gains  

---

## License

MIT — see [LICENSE](LICENSE).

Personal / research use of *your* books is the intended path. Don’t ship fine-tunes of copyrighted textbooks you don’t have rights to.

---

## Status

**v0.1.0** — Phase 0 scaffold live on GitHub. Next: real page ingest + LLM student ([ROADMAP.md](ROADMAP.md)).

```bash
git clone https://github.com/riacheruvu/bookworm-bot.git
cd bookworm-bot
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
bookworm run
```

Have fun teaching machines to hit the books.
