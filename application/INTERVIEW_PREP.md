# Interview & talking-point prep

Their process (from the posting): (1) application + reference check → (2) technical assessments & interviews
→ (3) a research discussion. So prep three modes: talk about your work, do Python/ML technicals, discuss research.

Golden rule for all of it: be concrete, be honest about gaps, and show HOW you learn. "I hadn't done X, so I
did Y to figure it out" beats pretending. Anthropic values clear communication and intellectual honesty.

---

## 1. Your three project stories (practice each out loud in ~90 seconds)

Use this shape each time: Problem → What I built → Hardest part → What I learned / would do next.

### Access-Stack (lead with this — it's your research bridge)
- Problem: comparing model behavior by "vibe" doesn't scale or hold up.
- Built: a Python toolkit to run the same prompts/specs across many local + cloud models and compare.
- Hardest part: [fill — e.g., normalizing outputs across models / adapter differences].
- Next: turn it into a real eval — [your cross-model spec-adherence study].

### pgpt stack
- Problem: wanted a fully private, self-hosted AI setup I actually control.
- Built: PrivateGPT + Ollama (22+ models) + Nginx/Redis/Prometheus/Grafana in Docker, plus an Electron chat client.
- Hardest part: [fill — networking between containers / healthchecks / streaming].
- Shows: I can stand up and operate real multi-service infrastructure.

### Dia3
- Problem: can an AI author game content safely without destabilizing a shipping build?
- Built: AI authors content as DATA (JSON/DataAssets); native C++ consumes it at runtime. MCP server + Docker bridge.
- Hardest part: the architectural rule (AI writes data, not runtime code).
- Shows: systems thinking + the discipline to separate concerns.

## 2. "Why AI safety / why Anthropic" — your honest narrative
- I build AI systems daily; operating them is what made the capability-vs-reliability gap concrete for me.
- I'm self-taught and I learn by building; the Fellowship's "fund builders, turn them into researchers" model is my bridge.
- I keep gravitating to evaluation/interpretability on my own (Access-Stack, SpecStack) — that's not a stretch, it's what I already do.
- [Add: one Anthropic paper you read and one genuine reaction to it.]

## 3. Technical topics to review (ML Systems + general)
- Python fluency: data structures, generators, async, typing, clean code. (They REQUIRE Python fluency — be sharp.)
- ML basics you should be able to explain simply: what a transformer does, attention, training vs inference,
  fine-tuning vs prompting, what LoRA/QLoRA do, tokens/context, overfitting, train/val/test.
- LLM eval: how you'd measure if a model follows a spec; pitfalls (contamination, prompt sensitivity, judging).
- Systems: REST APIs, Docker, latency vs throughput, batching, why serving big models needs many GPUs (memory).
- Be ready to write/reason about small Python live. Practice on a whiteboard/plain editor, thinking out loud.

## 4. Research-discussion prep
- Pick ONE paper you read well (see READING_LIST.md — model-specs or interpretability).
- Be ready to: summarize it in 3 sentences, say one thing you'd question, and propose a small follow-up
  experiment you could run with public models/APIs. (Your Access-Stack spec-adherence idea works here.)
- It's fine to say "I don't know" — then show how you'd find out.

## 5. Behavioral / story bank (have 2–3 ready)
- A time you were stuck and taught yourself out of it.
- A time you scoped something down to ship it (your CH06 lesson — great story about judgment).
- Why you care about this beyond a paycheck.

## 6. Practice drills (do these out loud)
- 90-sec Access-Stack pitch, no notes.
- "Walk me through what happens when you send a prompt to a served LLM."
- "How would you test whether two models differ in following a behavioral spec?"
- "Explain LoRA to a smart non-expert."
- "Tell me about a project that failed or got messy, and what you changed."
