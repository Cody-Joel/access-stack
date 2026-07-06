"""
tests/test_basics.py — Smoke tests to verify the toolkit loads and runs.
"""

import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_scenario_categories_load():
    from speclab.runner import SCENARIO_CATEGORIES
    assert "honesty_vs_helpfulness" in SCENARIO_CATEGORIES
    assert "safety_vs_autonomy" in SCENARIO_CATEGORIES
    for cat, scenarios in SCENARIO_CATEGORIES.items():
        assert len(scenarios) >= 1
        for s in scenarios:
            assert "id" in s
            assert "setup" in s
            assert "tension" in s
            assert "question" in s


def test_example_transcripts_load():
    from sentinelbench.runner import EXAMPLE_TRANSCRIPTS
    assert len(EXAMPLE_TRANSCRIPTS) >= 4
    for name, t in EXAMPLE_TRANSCRIPTS.items():
        assert "blind_spot" in t
        assert "is_harmful" in t
        assert "transcript" in t
        assert len(t["transcript"]) > 50


def test_score_answer():
    from skillforge.runner import score_answer
    score, matched = score_answer("the function yields control to the event loop", ["event loop", "yields", "non-blocking"])
    assert score > 0.5
    assert "event loop" in matched
    assert "yields" in matched


def test_score_answer_empty():
    from skillforge.runner import score_answer
    score, matched = score_answer("", ["event loop", "yields"])
    assert score == 0.0
    assert matched == []


def test_output_dirs_exist():
    dirs = [
        Path("speclab/results"),
        Path("sentinelbench/results"),
        Path("skillforge/results"),
    ]
    for d in dirs:
        assert d.exists(), f"Missing output dir: {d}"


def test_env_example_exists():
    assert Path(".env.example").exists()


def test_claude_usage_exists():
    assert Path("CLAUDE_USAGE.md").exists()
