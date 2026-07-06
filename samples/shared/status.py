"""
shared/status.py — Check that the environment is ready to run experiments.
Verifies: Anthropic API key, Ollama connectivity, Python deps, output dirs.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def check_anthropic_api() -> tuple[bool, str]:
    """Check if the Anthropic API key is set and valid."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return False, "ANTHROPIC_API_KEY not set — add it to your .env file"
    if not key.startswith("sk-ant-"):
        return False, "ANTHROPIC_API_KEY looks malformed (should start with sk-ant-)"
    return True, f"API key found (ending in ...{key[-6:]})"


def check_ollama() -> tuple[bool, str]:
    """Check if Ollama is running locally."""
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True, "Ollama is running at localhost:11434"
    except Exception:
        return False, "Ollama not reachable — run 'ollama serve' first"


def check_ollama_models() -> tuple[bool, str]:
    """List available Ollama models."""
    try:
        import urllib.request
        import json
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            data = json.loads(r.read())
        models = [m["name"] for m in data.get("models", [])]
        if not models:
            return False, "No models pulled yet — run 'ollama pull llama3' or 'ollama pull qwen2'"
        return True, f"Available models: {', '.join(models[:5])}"
    except Exception:
        return False, "Could not list models"


def check_python_deps() -> tuple[bool, str]:
    """Check required Python packages are installed."""
    required = ["anthropic", "rich", "matplotlib", "pandas", "pytest"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        return False, f"Missing packages: {', '.join(missing)} — run: pip install {' '.join(missing)}"
    return True, "All required packages installed"


def check_output_dirs() -> tuple[bool, str]:
    """Ensure output directories exist."""
    dirs = ["speclab/results", "sentinelbench/results",
            "skillforge/results", "notebooks"]
    missing = [d for d in dirs if not Path(d).exists()]
    if missing:
        for d in missing:
            Path(d).mkdir(parents=True, exist_ok=True)
        return True, f"Created missing output dirs: {', '.join(missing)}"
    return True, "All output directories present"


def print_status():
    """Print a formatted status report."""
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
    except ImportError:
        _plain_status()
        return

    table = Table(
        title="[bold]cipher-fellows — Environment Status[/bold]", show_header=True)
    table.add_column("Check", style="cyan", width=28)
    table.add_column("Status", width=8)
    table.add_column("Detail", style="dim")

    checks = [
        ("Anthropic API key", check_anthropic_api),
        ("Ollama server", check_ollama),
        ("Ollama models", check_ollama_models),
        ("Python packages", check_python_deps),
        ("Output directories", check_output_dirs),
    ]

    all_ok = True
    for name, fn in checks:
        ok, msg = fn()
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, status, msg)
        if not ok:
            all_ok = False

    console.print()
    console.print(table)
    console.print()
    if all_ok:
        console.print(
            "[green]Everything looks good — you're ready to run experiments.[/green]")
    else:
        console.print(
            "[yellow]Fix the issues above, then re-run: python main.py status[/yellow]")
    console.print()


def _plain_status():
    checks = [
        ("Anthropic API key", check_anthropic_api),
        ("Ollama server", check_ollama),
        ("Ollama models", check_ollama_models),
        ("Python packages", check_python_deps),
        ("Output directories", check_output_dirs),
    ]
    print("\n=== cipher-fellows status ===\n")
    for name, fn in checks:
        ok, msg = fn()
        symbol = "OK" if ok else "FAIL"
        print(f"[{symbol}] {name}: {msg}")
    print()
