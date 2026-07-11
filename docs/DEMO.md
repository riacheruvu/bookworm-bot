# Bookworm Bot — demo text

Copy-paste friendly blurbs for README, talks, issues, and “watch me hack” videos.  
**$0 path:** everything below works with the mock student (`bookworm run`).

---

## One-liner

**Bookworm Bot teaches an AI to study:** fail probes → find skill gaps → read book pages → practice → measure if it got better.

---

## Elevator (30 seconds)

Most “AI that reads” demos just stuff a PDF into a chatbot. Bookworm Bot is different. The agent has to **take a quiz**, **admit what it failed**, **study specific textbook pages**, then **retake practice problems**. We score whether reading the right pages fixed the right mistakes — not whether it sounds smart. No paid API keys required: mock student offline, or free local Ollama if you want.

---

## Elevator (90 seconds)

Imagine a student who can’t hand-wave their way through homework.

1. **Probe** — short, graded questions on a skill graph (units, free-body diagrams, Newton’s laws…).  
2. **Diagnose** — failures become skill gaps, not vibes. Prerequisites get priority.  
3. **Study** — the agent is sent to *book pages* (markdown mocks today; phone photos later), not an infinite web crawl.  
4. **Practice** — new attempts on the weak skills.  
5. **Evaluate** — heatmap + pre/post accuracy. Did studying help?

That’s the whole product thesis in one loop. Serious mode keeps grading strict. Exploratory mode lets the agent invent wilder questions when you want to play. Embodiment (Reachy Mini looking at a real book) is a later layer — the learning science works on a laptop first.

---

## Tagline options

- Hit the books. Measure the gain.  
- Learn like a student: fail, read, retry.  
- Gaps from failures. Knowledge from pages.  
- Curriculum, not context stuffing.  
- $0 to start. Books before the web.

---

## GitHub About blurb

```
AI agent that learns by reading books: probe → study pages → practice → get better. Local-first, no API keys required.
```

**Topics:** `ai-agents` `education` `llm` `local-first` `robotics` `self-improvement`

---

## README “Try it” block

```bash
git clone https://github.com/riacheruvu/bookworm-bot.git
cd bookworm-bot
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"

bookworm doctor    # mock always works; Ollama optional & free
bookworm run       # full learning loop on mechanics_demo
```

You should see: diagnosed gaps → pages studied → skill heatmap → “improved after study” when practice beats the first probe.

---

## Live demo script (3–5 min)

**Setup (before audience):** terminal open in repo, venv active.

### Beat 1 — The pitch (30s)

> “This isn’t RAG over a textbook. It’s a *study loop*. Watch the agent bomb a quiz, get sent to specific pages, then improve.”

### Beat 2 — Doctor (15s)

```bash
bookworm doctor
```

> “Default path is free. Mock student needs no keys. Ollama is optional if you already run local models.”

### Beat 3 — Serious run (2 min)

```bash
bookworm run -d mechanics_demo -m serious
```

Narrate as it scrolls:

> “Phase one: probes. It’s missing free-body diagrams and Newton’s second law…”  
> “Study plan points at concrete pages — not ‘search the internet’.”  
> “It reads free-body diagrams, Newton, friction…”  
> “Practice accuracy vs probe accuracy — that’s our north star metric.”

Call out the line:

> **Signal: improved after study ✓**

### Beat 4 — Exploratory flavor (45s)

```bash
bookworm run -m exploratory --probe-limit 4
```

> “When we’re exploring, probes can go soft and the agent can invent variants. Serious mode is for measurement; exploratory is for curiosity.”

### Beat 5 — Open the hood (30s)

Show quickly:

- `data/domains/mechanics_demo/skills.yaml` — skill graph  
- `probes.json` — graded questions  
- `pages/*.md` — “textbook” content  

> “Swap in your own domain by copying this folder. Your book, your probes, same loop.”

### Beat 6 — Close (15s)

> “Next: real page photos with local OCR, then maybe a desk robot that *looks* at the book. But the science is already here: **did the right reading fix the right failures?**”

---

## Sample session narration (voiceover)

> Session start. Domain: intro classical mechanics. Mode: serious.
>
> The student sits a six-question probe. Units of force? Sometimes. Free-body diagram definition? No. Net force on a 2 kg block? It guesses zero — classic underprepared energy.
>
> Gap assessor lights up: free-body diagrams, Newton’s second law, friction. Prerequisites bubble first.
>
> Study plan: page_fbd, page_newton, page_friction. The agent “opens” the mock textbook. Isolate the body. Draw external forces only. F equals m a. Static friction up to mu_s N.
>
> Practice round. Same skills, fresh attempts. Answers tighten. Heatmap greens. Probe accuracy was a third; practice is clean.
>
> Lesson logged: reading targeted pages beat vibes-based studying. Session saved. Onto the next chapter when we’re ready.

---

## Tweet / short post

```
Built a small project: Bookworm Bot.

AI doesn’t just “chat over a PDF.”
It fails a quiz → finds skill gaps → reads specific book pages → practices → we measure if it improved.

Local-first. No paid API keys.
mock student offline, optional free Ollama.

https://github.com/riacheruvu/bookworm-bot
```

---

## Longer social / blog lede

Most agents treat knowledge like a search box: retrieve a chunk, sound confident, move on.

Bookworm Bot treats knowledge like **school**.

You only get credit for skills you can demonstrate on probes. Miss a free-body diagram question and you don’t get a motivational quote — you get sent to the free-body diagram page. After you study, you practice. If the heatmap doesn’t move, the session didn’t work, no matter how eloquent the notes were.

That’s a stricter bar than “the summary looks nice,” and it’s more interesting. It also stays honest about cost: the default demo runs offline with a mock student. When you want real language, point it at a free local model. Cloud keys can wait.

Physical books, camera frames, Reachy Mini on a desk — those are later chapters. Chapter one is the loop.

---

## FAQ (demo Q&A)

**Is this just RAG?**  
No. Retrieval can help later, but the core is *curriculum + evaluation*: fail → study → retest.

**Do I need an API key?**  
No. `bookworm run` uses a mock student. Optional free upgrade: Ollama.

**Where’s the robot?**  
Embodiment is Phase 4. Learning loop is Phase 0–2. Mock the book with text/images first.

**Can I use my own textbook?**  
Yes. Copy `data/domains/mechanics_demo`, write skills, probes, and pages. Respect copyright for anything you publish or fine-tune.

**How do you know it “learned”?**  
Pre/post accuracy and per-skill heatmaps — not self-report.

---

## Slide titles (if you make a deck later)

1. Books before the web  
2. Gaps from failures, not vibes  
3. The loop: probe → diagnose → study → practice → evaluate  
4. Serious vs exploratory probes  
5. $0 stack: mock → Ollama → local OCR  
6. What’s next: photos, envs, Reachy Mini  

---

## Placeholder for a demo GIF caption

```
bookworm run — probe 33% → study three pages → practice 100%. Signal: improved after study.
```
