# Roadmap & scope

Living plan for [bookworm-bot](https://github.com/riacheruvu/bookworm-bot).  
**North star:** measure whether *reading the right book pages* reduces the *right failures*.

```
probe → diagnose gaps → study pages → practice → evaluate
         (+ optional env / robot later)
```

### Constraint: stingy / $0 first

**Paid API keys are never required.** Happy path:

1. **mock student** (default) — works offline, $0  
2. **Ollama** — free local LLM when you want real answers  
3. **Local OCR / VLM** — Tesseract, Ollama vision, etc.  

Cloud APIs are optional power-user extras only. Details: [docs/LOCAL_STACK.md](docs/LOCAL_STACK.md).

---

## In scope (product)

| In | Out (for now) |
|----|----------------|
| Skill graphs + probe banks | Full textbook OCR product |
| Mock + real page intake (images) | Training frontier foundation models |
| Gap diagnosis from **failures** | Relying on “I feel weak at X” self-report |
| Memory / notes / optional **local** LoRA with eval gates | Unrestricted web fine-tune as default |
| Parametric practice envs | Free-form “invent any universe” sims day one |
| Reachy Mini as camera + social UI | Full mobile manipulator research stack |
| Serious / exploratory / flexible probe modes | Shipping copyrighted book weights |
| Free local backends (mock, Ollama) | Required OpenAI/Anthropic keys |

---

## Phases

### Phase 0 — Scaffold ✅

- [x] Package + CLI (`bookworm run`)
- [x] Models: skills, probes, sessions
- [x] Loop: probe → diagnose → study → practice → eval
- [x] Probe modes: serious / exploratory / flexible
- [x] Demo domain `mechanics_demo`
- [x] Session JSON persistence
- [x] Tests for grading + loop
- [x] Free backends: `mock` (default) + optional `ollama`
- [x] `bookworm doctor` + [docs/LOCAL_STACK.md](docs/LOCAL_STACK.md)

### Phase 1 — Real reading (next, still free)

**Goal:** drop phone photos of book pages and get structured study notes **without cloud bills**.

- [ ] `Page.image_path` → OCR pipeline (Tesseract first)
- [ ] Optional Ollama vision for diagrams
- [ ] Page → skill tagging (manual seed + local model suggest)
- [ ] Study notes quality checks (quiz-from-page consistency)
- [ ] CLI: `bookworm ingest-pages ./photos/`

**Success:** agent chooses pages for gaps; notes are faithful enough that practice gains track real content.

### Phase 2 — Better students (local-first)

**Goal:** smarter student without breaking measurement or requiring paid keys.

- [x] Free local LLM backend (Ollama)
- [ ] External judge via Ollama for exploratory probes
- [ ] Persistent memory store (notes, formulas, worked examples)
- [ ] Optional **local** LoRA with **promote-only-if-eval-wins**
- [ ] Web fallback **gated** (only after book plan fails; still optional)

**Success:** held-out serious-mode accuracy rises across sessions; exploratory stays fun without polluting metrics.

### Phase 3 — Dynamic practice envs

**Goal:** skill gaps generate *parametric* tasks, not vibes.

- [ ] `EnvSpec` schema (μ, mass, incline, goals…)
- [ ] Template library mapped from skills
- [ ] `generate_env_for_gaps(skill_ids) → EnvSpec[]`
- [ ] Simple runner + scores folded into practice phase
- [ ] Optional viz (matplotlib / browser)

**Success:** after reading friction pages, env params stress μ_s / μ_k; failure modes shrink.

### Phase 4 — Embodiment (Reachy Mini)

**Goal:** physical sample stream + shareable demo.

- [ ] Camera frame → page ingest (reuse Phase 1)
- [ ] “Study session” narration (mic/speaker)
- [ ] Head/gaze toward book / whiteboard
- [ ] Tiny desk tasks that apply a learned skill
- [ ] Sim path so contributors need no hardware

**Success:** one demo video: fail probes → look at book → practice → better heatmap.

---

## Near-term backlog (hack-friendly)

**P0 — this week energy**

1. Polish GitHub README / topics  
2. ~~LLM student~~ → free **Ollama** backend + mock default (done)  
3. `bookworm report <session.json>` richer CLI  
4. Second domain (pick one): electronics, Python, or probability  

**P1 — next**

5. Image page ingest (**Tesseract / Ollama vision** — not paid APIs)  
6. Skill heatmap HTML export  
7. Probe authoring helper (`bookworm new-probe`)  
8. Eval harness: multi-session learning curves  

**P2 — research-flavored**

9. On-policy practice distillation dataset export  
10. Auto-curriculum: agent proposes next probes under flexible mode  
11. Env generation from notes  
12. Reachy Mini integration spike  

---

## Metrics we care about

| Metric | Why |
|--------|-----|
| Probe accuracy (pre) | Baseline ignorance |
| Practice / post accuracy | Did study help? |
| Per-skill heatmap | Right gaps fixed? |
| Pages used vs gaps | Efficient study? |
| Adapter vs baseline (later) | Was FT worth it? |

Vanity metrics we ignore early: tokens used, pages scraped, “sounds smart.”

---

## Design constraints (non-negotiable)

1. **Grade outside the student** — no self-scoring homework.  
2. **Books before web** for deliberate study.  
3. **Eval gates** before any weight update ships.  
4. **Mock first, body later** — robots don’t block learning science.  
5. **User’s library** — respect copyright; personal models from personal books.

---

## Open questions

- Default domain after mechanics: coding vs physics vs user-uploaded PDF?  
- Judge model for exploratory mode: same as student or smaller/cheaper?  
- LoRA target: skill-specific adapters vs one growing adapter?  
- Reachy Mini lite vs wireless for first camera path?  

Capture decisions in issues as we go.

---

## Suggested GitHub hygiene

- **Issues:** one phase epic + small tasks  
- **Labels:** `phase-1`, `good-first-hack`, `research`, `robot`  
- **Topics:** `ai-agents`, `education`, `fine-tuning`, `robotics`, `llm`  
- **Projects:** single board “Bookworm loop”
