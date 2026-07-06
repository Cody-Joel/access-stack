"""batch_eval.py — headless, free, resumable batch runner for SpecStack.

Runs the value-tradeoff scenarios across BOTH system-prompt conditions
(rules-only vs rules-with-explanation) and multiple models, appending every
result to a JSONL file as it goes — so a crash, a reboot, or a Windows reinstall
can never wipe completed runs. Uses local Ollama models (free, unlimited) by
default; no paid API is called in the loop.

This tests the core SpecStack hypothesis at scale: does giving a model the
*reasoning* behind its values (not just the rules) reduce how much models
diverge on hard value-tradeoff scenarios?

Usage:
    python batch_eval.py                                  # local models, 3 repeats
    python batch_eval.py --models llama2 mistral neural-chat --repeats 10
    python batch_eval.py --models groq/llama3-70b-8192 gemini/gemini-2.0-flash

Analyze the JSONL afterward (each line is one run) however you like.
"""

import argparse
import json
import time
import datetime
import urllib.request
from pathlib import Path

from SpecStack.runner import (
    SCENARIO_CATEGORIES,
    SYSTEM_PROMPT_RULES_ONLY,
    SYSTEM_PROMPT_WITH_EXPLANATION,
    call_model,
)

CONDITIONS = {
    "rules_only": SYSTEM_PROMPT_RULES_ONLY,
    "with_explanation": SYSTEM_PROMPT_WITH_EXPLANATION,
}


def collect_scenarios(category: str = "all") -> list:
    if category == "all":
        out = []
        for cat, items in SCENARIO_CATEGORIES.items():
            out.extend({**s, "category": cat} for s in items)
        return out
    return [{**s, "category": category} for s in SCENARIO_CATEGORIES.get(category, [])]


REMOTE_PREFIXES = ("groq/", "gemini/", "openrouter/", "anthropic/", "claude")


def is_remote(model: str) -> bool:
    """These models come from an external API, not Ollama, so don't validate them against Ollama."""
    return model.startswith(REMOTE_PREFIXES)


def available_models() -> set:
    """Model names Ollama currently serves (local + cloud). Empty set if Ollama is unreachable."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=10) as resp:
            data = json.loads(resp.read())
        return {m.get("name", "") for m in data.get("models", [])}
    except Exception:
        return set()


def main() -> None:
    ap = argparse.ArgumentParser(description="Batch runner for SpecStack value-tradeoff evals.")
    ap.add_argument("--models", nargs="+",
                    default=["gpt-oss:20b-cloud", "deepseek-v3.2:cloud", "qwen3.5:cloud",
                             "glm-5:cloud", "kimi-k2.6:cloud"],
                    help="Model specs: bare name = local Ollama; :cloud = Ollama cloud; or groq/..., gemini/...")
    ap.add_argument("--category", default="all", help="Scenario category, or 'all'.")
    ap.add_argument("--repeats", type=int, default=3, help="Runs per scenario/condition/model.")
    ap.add_argument("--sleep", type=float, default=0.3, help="Pause between calls (seconds).")
    ap.add_argument("--out", default=None, help="Output JSONL path (default: SpecStack/results/batch_<ts>.jsonl).")
    ap.add_argument("--list-models", action="store_true", help="List models Ollama has, then exit.")
    args = ap.parse_args()

    if args.list_models:
        avail = available_models()
        if not avail:
            print("Couldn't reach Ollama at localhost:11434 — is it running?")
        else:
            print("Available Ollama models:")
            for m in sorted(avail):
                print("  " + m)
        return

    # Skip any requested model Ollama doesn't actually have, so one typo doesn't waste a whole run.
    avail = available_models()
    if avail:
        missing = [m for m in args.models if not is_remote(m) and m not in avail]
        if missing:
            print(f"WARNING: not in Ollama, skipping: {missing}")
            print("  (run  python batch_eval.py --list-models  to see exact names)")
            args.models = [m for m in args.models if is_remote(m) or m in avail]
        if not args.models:
            print("No usable models left. Use --list-models to see what you have.")
            return

    scenarios = collect_scenarios(args.category)
    if not scenarios:
        print(f"No scenarios for category '{args.category}'.")
        return

    out_path = Path(args.out) if args.out else (
        Path("SpecStack/results") / f"batch_{datetime.datetime.now():%Y%m%d_%H%M%S}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(scenarios) * len(CONDITIONS) * len(args.models) * args.repeats
    print(f"Models: {args.models}")
    print(f"Scenarios: {len(scenarios)} | conditions: {len(CONDITIONS)} | repeats: {args.repeats}")
    print(f"Planned runs: {total}  ->  {out_path}\n")

    done = 0
    errors = 0
    with open(out_path, "a", encoding="utf-8") as f:
        for scen in scenarios:
            user_msg = f"{scen['setup']}\n\n{scen['tension']}\n\n{scen['question']}"
            for cond_name, sys_prompt in CONDITIONS.items():
                for model in args.models:
                    for rep in range(args.repeats):
                        t0 = time.time()
                        resp = call_model(model, sys_prompt, user_msg)
                        is_err = resp.startswith("[ERROR")
                        errors += is_err
                        rec = {
                            "scenario_id": scen["id"],
                            "category": scen["category"],
                            "condition": cond_name,
                            "model": model,
                            "repeat": rep,
                            "response": resp,
                            "error": is_err,
                            "latency_s": round(time.time() - t0, 2),
                            "ts": datetime.datetime.now().isoformat(),
                        }
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        f.flush()  # every run is saved immediately — nothing lost on a crash
                        done += 1
                        if done % 10 == 0 or done == total:
                            print(f"  {done}/{total}  (errors: {errors})  last: {model} / {cond_name} / {scen['id']}")
                        time.sleep(args.sleep)

    print(f"\nDone. {done} runs saved ({errors} errors) -> {out_path}")
    print("Each line is one JSON record. Next: summarize divergence between the two conditions.")


if __name__ == "__main__":
    main()
