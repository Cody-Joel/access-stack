# Access-Stack — Architecture & Design Patterns

## Overview

Access-Stack is organized into four independent Python packages plus a shared desktop UI. Each component can run standalone via CLI or through the PyQt5 desktop app.

```
access-stack.py          ← desktop UI (imports nothing from the stacks)
SpecStack/               ← evaluation framework #1
Sentinel-Stack/          ← evaluation framework #2
SkillStack/              ← evaluation framework #3
ONNX/                    ← C# local inference (separate project)
```

---

## Design pattern: Provider router

Every evaluation component routes API calls through a single `call_model(model_spec, system, user)` function. The `model_spec` string encodes both provider and model:

```python
# Pattern: "provider/model-id"
"groq/llama3-70b-8192"           # → Groq API
"gemini/gemini-2.0-flash"        # → Google Gemini
"anthropic/claude-sonnet-5"      # → Anthropic
"openrouter/meta-llama/..."      # → OpenRouter
"llama3"                         # → local Ollama (no prefix = Ollama)
```

This lets experiment scripts switch providers by changing one string. No provider-specific code leaks into the experiment logic.

Implementation in `SpecStack/runner.py`:
```python
def call_model(model_spec: str, system_prompt: str, user_message: str) -> str:
    if model_spec.startswith("groq/"):
        return _call_groq(model_spec[5:], system_prompt, user_message)
    elif model_spec.startswith("gemini/"):
        return _call_gemini(model_spec[7:], system_prompt, user_message)
    elif model_spec.startswith("anthropic/") or model_spec.startswith("claude"):
        return _call_claude(model_spec.replace("anthropic/", ""), system_prompt, user_message)
    else:
        return _call_ollama(model_spec, system_prompt, user_message)
```

Each provider function is a pure HTTP call — no SDK dependency except Anthropic (which has no REST-only path for streaming). Groq, Gemini, and Ollama all use `urllib.request` with no third-party packages.

---

## Design pattern: Two-condition experiment

SpecStack's core insight: to measure whether a prompt variable affects behavior, run the same model on the same scenario under two conditions and compare. The runner handles this automatically:

```python
for model in models:
    for condition in ["rules_only", "with_explanation"]:
        system = SYSTEM_PROMPT_RULES_ONLY if condition == "rules_only" else SYSTEM_PROMPT_WITH_EXPLANATION
        response = call_model(model, system, scenario_message)
        results.append({
            "scenario_id": scenario["id"],
            "condition": condition,
            "model": model,
            "response": response,
            ...
        })
```

Output is JSONL (one result per line) so runs can be appended, filtered, and analyzed without loading the full file.

---

## Design pattern: Labeled transcript evaluation

SentinelBench evaluates whether a monitor can correctly classify transcripts it's never seen during training. Every transcript has a ground-truth label (`is_harmful: true/false`) and a blind-spot category. The runner:

1. Sends the transcript to the monitor model with a structured system prompt
2. Parses the monitor's JSON response (`suspiciousness_score`, `flagged`, `blind_spot_exploited`)
3. Compares `flagged` to `is_harmful` to compute `correct`
4. Reports catch rate (harmful transcripts correctly flagged) and false-positive rate (benign transcripts incorrectly flagged)

The monitor system prompt is deliberately generic — it doesn't hint at the blind-spot categories being tested. This tests whether the monitor notices subtle attacks without being told what to look for.

---

## Design pattern: Offline-first, cloud-optional

Every component works with local Ollama and zero API keys:
- SpecStack: `python runner.py --demo` uses `llama3` (local Ollama) by default
- SentinelBench: falls back to error messages if no key, never crashes
- Desktop UI: Status tab shows what's available and what's missing

API calls are isolated in provider functions that return error strings (not exceptions) on failure. This means UI code never needs try/except around model calls — the error string is displayed like any other response.

---

## Design pattern: QThread for all network I/O

The PyQt5 desktop UI never blocks the main thread. Every API call runs in a worker:

```python
class ChatWorker(QThread):
    def __init__(self, model, system, user):
        super().__init__()
        self.signals = WorkerSignals()  # QObject with pyqtSignal fields

    def run(self):
        result = call_model(self.model, self.system, self.user)
        self.signals.result.emit(result)
        self.signals.finished.emit()
```

The pattern:
1. Worker class inherits `QThread`
2. Signals are defined on a separate `QObject` (required by PyQt5 — signals can't be defined on QThread directly without extra metaclass handling)
3. The UI connects to signals before calling `worker.start()`
4. `finished` signal re-enables the Send button

---

## Design pattern: Flat color system

All UI colors are defined once in a `COLORS` dict at the top of `access-stack.py`. No color values appear anywhere else in the file. The stylesheet is an f-string that interpolates from `COLORS`.

```python
COLORS = {
    "bg":      "#0d0f14",   # main background
    "panel":   "#131620",   # sidebar, tab pane
    "surface": "#1b1f2e",   # input fields, table rows
    "border":  "#252a3d",   # all borders
    "accent":  "#4f8ef7",   # primary action color
    "green":   "#22d3a5",   # success, Ollama running
    "yellow":  "#f59e0b",   # warning
    "red":     "#ef4444",   # error, danger
    "text":    "#e2e8f0",   # primary text
    "muted":   "#64748b",   # secondary text, labels
}
```

This design matches Riff (WPF) and Op (WinUI 3) — same hex values across all three projects so the design language is consistent.

---

## Design pattern: Results as timestamped JSONL

All evaluation runners write results as timestamped files:

```python
output_path = Path(__file__).parent / "results" / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
```

- Path is relative to `__file__`, not `cwd` — so it works regardless of where you run the script from
- `mkdir(parents=True, exist_ok=True)` — no setup step needed
- Timestamped filenames prevent overwrites and make reruns easy to compare
- The Dashboard tab in the desktop UI reads `speclab_results/*.json` and displays a summary table

---

## ONNX component (C#)

`ONNX/OnnxEngine.cs` wraps Microsoft.ML.OnnxRuntime for local inference without Ollama. It's a separate `dotnet` project and can be run as a CLI or embedded as a library. It's independent of the Python components and doesn't share state.

Use case: ONNX lets you run quantized models on CPU/GPU without running an Ollama server — useful for embedded scenarios or environments where background services aren't available.

---

## File layout decisions

| Choice | Why |
|---|---|
| One `call_model()` per component (not shared) | Each component has slightly different timeout/error handling needs; sharing would require a common dependency |
| No `requirements.txt` in subpackages | All deps are in the root `requirements.txt`; subpackages are not installable packages |
| Scenarios in `scenarios.json` (separate from runner code) | Scenarios change more often than runner logic; separating them lets non-coders add scenarios |
| Results in `<component>/results/` (not a shared dir) | Each component owns its results; mixing them would require tagging every record with its source |
