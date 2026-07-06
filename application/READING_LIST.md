# ML / AI-safety reading list — curated for your workstreams

Goal: read 2–3 of these *well* (enough to discuss and to cite ONE in your essay). Don't try to read all.
Titles are stable — search them; most are free on arXiv or Anthropic's blog. (Recalled from memory; verify links.)

## Tier 0 — read first (mission + approachable)
1. Anthropic — "Core Views on AI Safety: When, Why, What, and How" (blog, 2023). Their framing in their words.
2. Amodei, Olah, et al. — "Concrete Problems in AI Safety" (2016). Foundational, readable, still cited.

## Tier 1 — your workstreams (ML Systems & Performance + evals)
3. Kaplan et al. — "Scaling Laws for Neural Language Models" (2020). Why scale matters.
4. Hoffmann et al. — "Training Compute-Optimal LLMs" (Chinchilla, 2022). Compute vs data trade-off.
5. Kwon et al. — "Efficient Memory Management for LLM Serving with PagedAttention" (vLLM, 2023). Real ML-systems.
6. Dao et al. — "FlashAttention" (2022). Performance engineering for transformers.

## Tier 2 — safety / evals / interpretability (your #2 preference)
7. Bai et al. — "Constitutional AI: Harmlessness from AI Feedback" (Anthropic, 2022).
8. Anthropic interpretability — "Toy Models of Superposition" (2022) and "Towards Monosemanticity" (2023).
9. Cited in the Fellows posting (so read at least one): "Subliminal Learning: LMs Transmit Behavioral Traits
   via Hidden Signals in Data"; "Stress-Testing Model Specs Reveals Character Differences among LMs";
   "Open-source circuits". The Model-Specs one is closest to your SpecStack — read that one.

## Tier 3 — hands-on for your 8GB GPU (read + implement)
10. Hu et al. — "LoRA: Low-Rank Adaptation of LLMs" (2021).
11. Dettmers et al. — "QLoRA: Efficient Finetuning of Quantized LLMs" (2023). This is what makes 8GB work.

## Foundational (if you want the ground truth of transformers)
12. Vaswani et al. — "Attention Is All You Need" (2017).

## How to use this
- Pick #2 + one of {#9 model-specs, #7} + one Tier-3 to actually implement.
- For each, jot: one sentence on the core idea, one thing you'd question or extend. That's your essay/interview ammo.
- Citing the model-specs paper in essay B (next to SpecStack) is a strong, honest move — it shows you found the
  connection yourself.
