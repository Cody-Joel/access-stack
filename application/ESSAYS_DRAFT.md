# Application essays — starting drafts (Cody Puchailo)

READ FIRST — integrity note:
Anthropic publishes "Guidance on Candidates' AI Usage" for applications. Check it and follow it.
These are NOT finished essays to paste in. They're honest scaffolds built from your real work, meant to
help you *articulate what you actually did and believe*. Rewrite every one in your own voice and words —
the specifics, the feeling, the reasons have to be genuinely yours. The application will be stronger AND
honest that way. I've left [brackets] where only you can fill the truth.

The portal (Constellation) has its own prompts; exact wording may differ. These cover the material almost
any version will ask for: motivation, a technical project, why Anthropic, and a small research idea.

---

## A. Motivation — "Why this work?"  (~150–220 words)

I'm a self-taught software engineer, and for the last two years almost everything I've built has been AI
systems — running local models, wiring them into tools, and getting them to do real work reliably. Doing
that daily is what turned an abstract interest in AI safety into a concrete one: when you actually operate
these models, you see how capable they are and how easily they do the wrong thing confidently. That gap —
between capability and reliability — is what I want to work on.

I don't come from a research background; I come from building. I taught myself full-stack development in an
intensive program, then kept going on my own into infrastructure, local LLMs, and evaluation. I learn by
making the thing and seeing where it breaks. The Fellowship's model — funding and mentorship to transition
builders into empirical researchers — is exactly the bridge I need, and the "regardless of previous
experience" part is why I'm applying instead of talking myself out of it.

[Add one or two sentences that are specifically YOURS: what first made you care about AI being safe/beneficial,
in your own words. This is the most important part — don't let it sound generic.]

---

## B. Technical project — your strongest, with YOUR contribution  (~200–300 words)

Lead with Access-Stack (it's closest to research). Structure: problem → what you built → what you found → what
it shows about you.

Over the past year I built Access-Stack, a toolkit for evaluating and comparing language models. The core
idea: run the same prompts and specifications across many models — local (via Ollama) and cloud — and compare
their behavior side by side, systematically instead of by vibe. One component, SpecStack, stress-tests a
model's behavior against a written specification to surface where models diverge from intended behavior —
which I later realized is adjacent to published model-spec evaluation work.

[Insert a concrete finding here — even a small one. Example shape: "Across N models on task X, I found that
___ diverged in ___ ways." A real result, even modest, is what makes this land. Run one comparison and
report it honestly.]

I built it in Python, [solo], designing the runner, the model adapters, and the comparison output myself.
Alongside it I've built related systems: a fully self-hosted private-AI stack (PrivateGPT + Ollama +
monitoring, orchestrated in Docker) and an AI-to-Unreal-Engine pipeline where an AI authors game content as
data consumed by native C++. The through-line is that I can take a fuzzy AI capability and turn it into a
working, reliable system — and I document as I go.

---

## C. Why Anthropic / research interest  (~120–180 words)

Anthropic is the lab whose framing I actually share: treating AI as an empirical science, and treating safety
as the point rather than an afterthought. The work I keep coming back to on my own — evaluating model
behavior, stress-testing against specs, understanding *why* a model does what it does — lines up most with
the evaluation and [interpretability / ML-systems] directions.

My preferred workstreams are ML Systems & Performance and AI Safety: I'm strongest at building the systems and
infrastructure that empirical research runs on, and I'm most motivated by using that to make models more
reliable and honest. [Name one specific piece of Anthropic research you actually read and what you thought —
this shows you did the work. Pick one from their Alignment Science / interpretability blog.]

---

## D. A small research idea (if asked for a proposal)  (~120–180 words)

Fellows use external infrastructure (open models, public APIs) — so the idea should be doable that way.

A cross-model specification-adherence study: take a written behavioral spec, derive a battery of test prompts
from it, and run it across 6–10 open and API models. Measure where and how they diverge from the spec —
consistency, refusal behavior, and failure modes — and characterize the differences. It's directly buildable
on the Access-Stack tooling I already have, uses only public models/APIs, and produces a concrete public
output (repo + writeup). [Sharpen the specific question you'd ask — the tighter and more honest, the better.]

---

## Notes for you
- Keep it plain and specific. Anthropic values clear communication and dislikes filler — no buzzwords.
- Your honest story (self-taught builder → wants to do empirical research) is a strength, not a weakness. Tell it straight.
- Everything above needs YOUR edit pass to be genuinely your voice and to satisfy the AI-usage policy.
