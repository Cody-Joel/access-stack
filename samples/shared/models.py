"""
shared/models.py — Unified model caller supporting Groq, Gemini, Ollama, and Anthropic.

Usage:
    from shared.models import call_model, list_available_providers

    response = call_model("groq/llama3-70b-8192", system_prompt, user_message)
    response = call_model("gemini/gemini-2.0-flash", system_prompt, user_message)
    response = call_model("ollama/llama3", system_prompt, user_message)
    response = call_model("anthropic/claude-sonnet-4-6", system_prompt, user_message)

Provider is determined by the prefix before the slash.
Falls back gracefully with a clear error message if a key is missing.
"""

import os
import json
import urllib.request
from typing import Optional


# ── Provider detection ─────────────────────────────────────────────────────────

def parse_model_string(model_str: str) -> tuple[str, str]:
    """Parse 'provider/model_name' into (provider, model_name)."""
    if "/" in model_str:
        parts = model_str.split("/", 1)
        return parts[0].lower(), parts[1]
    # Auto-detect by model name patterns
    model_lower = model_str.lower()
    if "gemini" in model_lower:
        return "gemini", model_str
    if any(x in model_lower for x in ["llama", "mixtral", "gemma", "qwen"]):
        # Could be groq or ollama — prefer groq if key exists
        if os.environ.get("GROQ_API_KEY"):
            return "groq", model_str
        return "ollama", model_str
    if "claude" in model_lower:
        return "anthropic", model_str
    return "ollama", model_str  # Default to local


def list_available_providers() -> dict:
    """Check which providers have API keys configured."""
    return {
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "groq": bool(os.environ.get("GROQ_API_KEY")),
        "gemini": bool(os.environ.get("GEMINI_API_KEY")),
        "ollama": _check_ollama_running(),
    }


def _check_ollama_running() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
        return True
    except Exception:
        return False


# ── Groq caller ────────────────────────────────────────────────────────────────
# Groq uses the OpenAI-compatible API format.
# Available free models: llama3-70b-8192, llama3-8b-8192, mixtral-8x7b-32768, gemma2-9b-it

GROQ_MODELS = [
    "llama3-70b-8192",      # Best quality, still fast
    "llama3-8b-8192",       # Faster, good for bulk runs
    "mixtral-8x7b-32768",   # Good reasoning, long context
    "gemma2-9b-it",         # Google's model via Groq
]

def call_groq(model: str, system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return "[ERROR: GROQ_API_KEY not set — get your free key at console.groq.com]"

    # Strip provider prefix if present
    if model.startswith("groq/"):
        model = model[5:]
    if model not in GROQ_MODELS:
        model = "llama3-70b-8192"  # Sensible default

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": temperature,
        "max_tokens": 1000
    }

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"[ERROR Groq HTTP {e.code}: {body[:200]}]"
    except Exception as e:
        return f"[ERROR Groq: {e}]"


# ── Gemini caller ──────────────────────────────────────────────────────────────
# Uses Google's REST API directly — no SDK needed.
# Free tier: 15 req/min for Flash, generous daily limit.

GEMINI_MODELS = [
    "gemini-2.0-flash",     # Fast, free, capable
    "gemini-1.5-flash",     # Slightly older but very reliable
    "gemini-1.5-pro",       # Slower but stronger reasoning
]

def call_gemini(model: str, system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "[ERROR: GEMINI_API_KEY not set — get your free key at aistudio.google.com]"

    if model.startswith("gemini/"):
        model = model[7:]
    if model not in GEMINI_MODELS:
        model = "gemini-2.0-flash"

    # Gemini REST API format
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_message}], "role": "user"}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 1000
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"[ERROR Gemini HTTP {e.code}: {body[:200]}]"
    except Exception as e:
        return f"[ERROR Gemini: {e}]"


# ── Ollama caller ──────────────────────────────────────────────────────────────

def call_ollama(model: str, system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
    if model.startswith("ollama/"):
        model = model[7:]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "options": {"temperature": temperature}
    }

    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["message"]["content"]
    except ConnectionRefusedError:
        return "[ERROR Ollama: server not running — start with 'ollama serve']"
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"[ERROR Ollama HTTP {e.code}: {body[:200]}]"
    except Exception as e:
        return f"[ERROR Ollama: {e}]"


# ── Anthropic caller ───────────────────────────────────────────────────────────

def call_anthropic(model: str, system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "[ERROR: ANTHROPIC_API_KEY not set]"

    if model.startswith("anthropic/"):
        model = model[10:]
    if not model:
        model = "claude-sonnet-4-6"

    payload = {
        "model": model,
        "max_tokens": 1000,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}]
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"[ERROR Anthropic HTTP {e.code}: {body[:200]}]"
    except Exception as e:
        return f"[ERROR Anthropic: {e}]"


# ── Unified caller ─────────────────────────────────────────────────────────────

def call_model(
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    fallback: Optional[str] = None
) -> str:
    """
    Call any model by provider-prefixed name.
    
    Examples:
        call_model("groq/llama3-70b-8192", system, user)
        call_model("gemini/gemini-2.0-flash", system, user)
        call_model("ollama/llama3", system, user)
        call_model("anthropic/claude-sonnet-4-6", system, user)
        call_model("llama3-70b-8192", system, user)   # auto-detects Groq
    
    If the primary call fails and fallback is set, tries fallback model.
    """
    provider, model_name = parse_model_string(model)

    callers = {
        "groq": call_groq,
        "gemini": call_gemini,
        "ollama": call_ollama,
        "anthropic": call_anthropic,
    }

    caller = callers.get(provider)
    if not caller:
        return f"[ERROR: Unknown provider '{provider}' in model string '{model}']"

    result = caller(model, system_prompt, user_message, temperature)

    # If primary failed and fallback given, try fallback
    if result.startswith("[ERROR") and fallback:
        print(f"  [retrying with fallback: {fallback}]")
        return call_model(fallback, system_prompt, user_message, temperature)

    return result


def get_best_available_model(prefer_quality: bool = True) -> str:
    """
    Return the best available model given current API keys.
    Used to auto-select a monitor model when none is specified.
    """
    providers = list_available_providers()

    if providers["anthropic"]:
        return "anthropic/claude-sonnet-4-6"
    if providers["groq"]:
        return "groq/llama3-70b-8192" if prefer_quality else "groq/llama3-8b-8192"
    if providers["gemini"]:
        return "gemini/gemini-2.0-flash"
    if providers["ollama"]:
        return "ollama/llama3"
    
    return "[ERROR: No API keys set and Ollama not running. Check your .env file.]"


# ── Convenience: print provider status ────────────────────────────────────────

def print_provider_status():
    providers = list_available_providers()
    print("\nAPI Provider Status:")
    for provider, available in providers.items():
        symbol = "✓" if available else "✗"
        hint = ""
        if not available:
            hints = {
                "anthropic": "→ set ANTHROPIC_API_KEY in .env",
                "groq": "→ set GROQ_API_KEY in .env (free at console.groq.com)",
                "gemini": "→ set GEMINI_API_KEY in .env (free at aistudio.google.com)",
                "ollama": "→ run 'ollama serve' in a terminal",
            }
            hint = hints.get(provider, "")
        status = "available" if available else "not configured"
        print(f"  [{symbol}] {provider:<12} {status}  {hint}")
    print()
    best = get_best_available_model()
    if not best.startswith("[ERROR"):
        print(f"  Best available model: {best}")
    else:
        print(f"  {best}")
    print()
