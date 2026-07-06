# Anthropic Fellows — Application Plan (Cody Puchailo)

One application. Rank workstream preferences. Rolling basis — apply as soon as it's genuinely strong.
Eligible: Canada ✓, Python-fluent ✓, no visa needed ✓.

## 1. Workstream ranking (what to put on the form)
1. ML Systems & Performance  ← primary
2. AI Safety                 ← strong secondary (SpecStack is your bridge)
3. Reinforcement Learning
(They consider you for all by default. Leave AI Security "open"; skip Economics.)

## 2. Application components — status
| # | Component | Status | Owner |
|---|-----------|--------|-------|
| 1 | Resume | DRAFTED (`resume.html`) — needs your placeholders | you fill, I polish |
| 2 | Public GitHub with 2–3 real projects | NOT READY (see §4) | you + me |
| 3 | Essays / short answers (motivation, why Anthropic, project) | NOT STARTED | I draft, you edit |
| 4 | One public "output" (an eval/finding writeup) | NOT STARTED — highest leverage (see §5) | we build |
| 5 | References | LIST THEM — course instructor? anyone technical | you |
| 6 | Workstream preferences + logistics (location, availability) | your info | you |

## 3. Resume — placeholders to fill
- Confirm name shown: "Cody Puchailo" (vs full "Cody Joel Puchailo")
- Location + work authorization (Canadian citizen / PR?) — eligibility-critical
- Course: is it a Diploma or Certificate? School name + dates
- LinkedIn URL — verify (you gave linked.com/cody-puchailo; likely linkedin.com/in/cody-puchailo)
- One concrete Access-Stack result once you run a comparison

## 4. GitHub — DO THIS CAREFULLY (security)
Your public code is the portfolio. Two problems: old account (git-addcommit) is locked; new one (CodyJoel) is empty.
- Decision: recover old OR push fresh to CodyJoel. Fresh is faster and cleaner.
- BEFORE pushing ANYTHING, scrub secrets. These must NEVER go public:
  - `C:\pgpt\.env`, any `.env` files, `C:\UEStack\wg-easy\wg0.conf` (VPN private keys)
  - API keys/tokens in configs
  - Add a `.gitignore`; keep the good code + READMEs.
- Priority repos: Access-Stack, pgpt (docs + non-secret code), Dia3, Riff.

## 5. The single highest-leverage move: produce ONE public output
The Fellowship is empirical research; ~80% of fellows produce a paper. You have zero papers today —
so the biggest jump in your candidacy is ONE small, real, public empirical result. Your Access-Stack is
the closest thing you have. Candidate mini-projects (pick ONE, keep it small):
- Run the same model-spec stress test across 5+ models via Access-Stack; write up where they diverge.
- Fine-tune a small model (Unsloth, your 8GB GPU) on a defined task; report before/after with numbers.
- A tiny reproduction of a published eval, with your results and a short honest writeup.
Output = a GitHub repo + a 1–2 page writeup. That's your "public output."

## 6. Honest technical steers
- KEEP THE AI/EVAL WORK IN PYTHON. The Fellowship requires Python fluency and research code is Python —
  rewriting Access-Stack in C++ would hurt this application. Save C++/C# for Dia3 and Riff (systems/games).
- Rename the stacks later, not now. "Sentinel/Skill/Spec-Stack" are fine working names; naming is not the
  bottleneck — a public result is.

## 7. How we actually execute (NOT 6 agents on a vague prompt)
Your own CH06 lesson: one session burned 290k tokens on plans and shipped nothing; a scoped one shipped a
working app. Same rule here. We do ordered slices, each producing one real artifact:
  Slice A: you fill resume placeholders → I finalize the PDF.
  Slice B: draft the essays from your real story (I write, you make it yours).
  Slice C: scrub + push one repo (Access-Stack) to github.com/CodyJoel.
  Slice D: build the ONE public output (§5).
  Slice E: assemble + submit.
A swarm of sub-agents on "finish everything" produces incoherent output and burns tokens. If we use agents,
it's ONE scoped agent per slice with a tight brief — not 6 at once.

## 8. Deferred (real, but not blocking the application)
- Riff UI overhaul (one-workspace redesign) — Riff is portfolio-ready as-is.
- Rewriting Access-Stack in C++/C#.
- taskforge polish.
