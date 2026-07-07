# Access-Stack — LLM Evaluation Toolkit

A Python toolkit for evaluating, comparing, and stress-testing language models. Three evaluation frameworks, one desktop UI, all running against local Ollama or cloud APIs.

## What's in here

| Component | What it does |
|---|---|
| **SpecStack** | Runs value-conflict scenarios across models. Measures behavioral divergence when models are given bare rules vs. explained values. |
| **SentinelBench** | Feeds synthetic adversarial agent transcripts to a monitor model. Measures whether the monitor catches subtle harmful actions — file reuse, counting errors, locale exploitation. |
| **SkillStack** | Presents coding tasks in AI-assisted vs. solo conditions, then quizzes for conceptual retention. Tests whether AI assistance trades speed for understanding. |
| **Desktop UI** | PyQt5 app with 7 tabs: Chat, SpecLab, SentinelBench, **SkillStack**, Dashboard, Tools, Status. All providers in one interface. |

## Quick start

```bash
cd C:\AS
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit .env with any API keys you want to use
python access-stack.py
```

To run the CLI evaluators directly:

```bash
# SpecStack — value-conflict scenarios
python SpecStack/runner.py --demo
python SpecStack/runner.py --category honesty_vs_helpfulness --models groq/llama3-70b-8192 gemini/gemini-2.0-flash

# SentinelBench — monitor blind spot detection
python Sentinel-Stack/runner.py --demo
python Sentinel-Stack/runner.py --transcript path/to/transcript.txt

# SkillStack — skill retention experiment
python SkillStack/runner.py --demo
```

## Providers supported

| Provider | Key env var | Cost |
|---|---|---|
| Ollama (local) | none — runs at localhost:11434 | free |
| Groq | `GROQ_API_KEY` | free tier (fast) |
| Gemini | `GEMINI_API_KEY` | free tier (2.0-flash 1500 req/day) |
| Anthropic | `ANTHROPIC_API_KEY` | paid |
| NVIDIA NIM | `NIM_API_KEY` | paid / self-hosted |
| OpenRouter | `OPENROUTER_API_KEY` | pay-per-token, many models |

No key needed to run local Ollama models. Get Groq and Gemini free keys at console.groq.com and aistudio.google.com.

## Results

SpecStack and SentinelBench write timestamped JSON to `SpecStack/results/` and `Sentinel-Stack/results/`. The Dashboard tab in the desktop UI loads and displays all past runs.

See [FINDINGS.md](FINDINGS.md) for results from real runs across 5 model families.

## Structure

```
access-stack.py          # Desktop UI (PyQt5)
Access-Stack-B.py        # Chat-focused alternate UI
models.json              # Provider/model registry
requirements.txt
.env.example             # Copy to .env, fill in keys

SpecStack/
  runner.py              # CLI — value-conflict stress tester
  scenarios.json         # Scenario definitions (extended set)
  results/               # Timestamped JSONL run outputs

Sentinel-Stack/
  runner.py              # CLI — monitor blind spot detector
  results/               # Timestamped JSON run outputs

SkillStack/
  runner.py              # CLI — skill retention experiment
  results/

ONNX/
  OnnxEngine.cs          # C# ONNX inference wrapper
  Program.cs             # Standalone CLI for local model inference

application/
  APPLICATION_PLAN.md    # Anthropic Fellows application plan
  ESSAYS_DRAFT.md        # Essay drafts (fill in your own voice)
  resume.html            # Resume template
```

## What's interesting technically

SpecStack's two-condition design is the core: the same scenario, same models, two different system prompts — one listing bare rules, one explaining the reasoning behind each value. The behavioral divergence between conditions is the finding. When models get the reasoning, their choices shift: on value-conflict scenarios where models previously scattered across options, adding the "why" produces measurable convergence toward the honest/direct answer.

SentinelBench exploits a real weakness in LLM-as-monitor safety patterns: monitors trained to catch overt harmful actions miss *subtle* harmful actions that are technically visible in the transcript but require careful tracking (file provenance, exact line numbers, locale-dependent behavior). The gap between overt-catch-rate and subtle-catch-rate is the finding.

## Security

Never commit `.env` files. The `.gitignore` blocks them. Before pushing this repo publicly:
- Confirm no API keys are hardcoded in source
- Confirm `wg0.conf` (if present anywhere) is excluded
- Run `grep -r "sk-ant-\|ANTHROPIC_API_KEY" . --include="*.py"` to verify
