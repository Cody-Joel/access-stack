"""
tests/test_timer.py — Unit tests for timer.py module.

Run with: pytest tests/test_timer.py -v
"""

import pytest
import json
import time
from pathlib import Path
from timer import (
    start_session,
    end_session,
    log_usage,
    get_session_seconds,
    get_model_metrics,
    get_all_model_metrics,
    get_summary,
    save_session,
    load_session,
)


class TestSessionLifecycle:
    """Test session start/end and timing."""

    def test_start_session_initializes(self):
        """start_session() should return an ISO timestamp."""
        session_id = start_session()
        assert session_id is not None
        assert "T" in session_id  # ISO format includes T
        assert len(session_id) > 10

    def test_get_session_seconds_increases(self):
        """get_session_seconds() should increase over time."""
        start_session()
        t1 = get_session_seconds()
        time.sleep(0.1)
        t2 = get_session_seconds()
        assert t2 > t1
        assert t2 - t1 >= 0.05  # Allow some margin

    def test_end_session_sets_timestamp(self):
        """end_session() should record an end time."""
        start_session()
        time.sleep(0.05)
        end_session()
        # get_summary() should now show a completed session
        summary = get_summary()
        assert "Session Summary" in summary


class TestLogUsage:
    """Test logging of API calls."""

    def test_log_usage_records_call(self):
        """log_usage() should record a model call."""
        start_session()
        log_usage("groq/llama3-70b", request_time_sec=0.234, tokens_estimated=150)

        metrics = get_model_metrics("groq/llama3-70b")
        assert metrics["call_count"] == 1
        assert metrics["total_tokens"] == 150
        assert abs(metrics["total_time_sec"] - 0.234) < 0.01

    def test_log_usage_aggregates_multiple_calls(self):
        """Multiple calls should aggregate correctly."""
        start_session()
        log_usage("groq/llama3-70b", 0.2, tokens_estimated=100)
        log_usage("groq/llama3-70b", 0.3, tokens_estimated=120)
        log_usage("groq/llama3-70b", 0.25, tokens_estimated=110)

        metrics = get_model_metrics("groq/llama3-70b")
        assert metrics["call_count"] == 3
        assert metrics["total_tokens"] == 330
        assert abs(metrics["avg_latency_sec"] - 0.25) < 0.01

    def test_log_usage_with_cost(self):
        """Cost should be recorded and summed correctly."""
        start_session()
        log_usage("anthropic/claude-opus", 0.5, tokens_estimated=200, provider_cost=0.015)
        log_usage("anthropic/claude-opus", 0.6, tokens_estimated=250, provider_cost=0.018)

        metrics = get_model_metrics("anthropic/claude-opus")
        assert metrics["call_count"] == 2
        assert abs(metrics["total_cost"] - 0.033) < 0.001


class TestModelMetrics:
    """Test per-model metric aggregation."""

    def test_get_model_metrics_empty(self):
        """Metrics for an unseen model should be zeros."""
        start_session()
        metrics = get_model_metrics("nonexistent/model")
        assert metrics["call_count"] == 0
        assert metrics["avg_latency_sec"] == 0.0
        assert metrics["total_tokens"] == 0
        assert metrics["total_cost"] == 0.0

    def test_get_all_model_metrics(self):
        """Should return metrics for all models in session."""
        start_session()
        log_usage("groq/llama3-70b", 0.2, tokens_estimated=100)
        log_usage("ollama/mistral", 0.5, tokens_estimated=80)
        log_usage("groq/llama3-70b", 0.25, tokens_estimated=110)

        all_metrics = get_all_model_metrics()
        assert "groq/llama3-70b" in all_metrics
        assert "ollama/mistral" in all_metrics
        assert len(all_metrics) == 2

        assert all_metrics["groq/llama3-70b"]["call_count"] == 2
        assert all_metrics["ollama/mistral"]["call_count"] == 1


class TestSummaryFormat:
    """Test get_summary() output format."""

    def test_get_summary_returns_markdown(self):
        """Summary should be valid markdown with table."""
        start_session()
        log_usage("groq/llama3-70b", 0.234, tokens_estimated=150)

        summary = get_summary()
        assert "## Session Summary" in summary
        assert "| Model | Calls |" in summary
        assert "groq/llama3-70b" in summary
        assert "| 1 |" in summary  # 1 call

    def test_get_summary_empty_session(self):
        """Summary of empty session should have helpful message."""
        start_session()
        summary = get_summary()
        assert "Session Summary" in summary
        assert "No API calls" in summary or "0" in summary

    def test_get_summary_multiple_models(self):
        """Summary should show all models in one table."""
        start_session()
        log_usage("groq/llama3-70b", 0.2, tokens_estimated=100)
        log_usage("ollama/mistral", 0.5, tokens_estimated=80)
        log_usage("groq/llama3-70b", 0.25, tokens_estimated=110)

        summary = get_summary()
        assert "groq/llama3-70b" in summary
        assert "ollama/mistral" in summary
        assert summary.count("| ") >= 6  # Header + 2 rows minimum


class TestSessionPersistence:
    """Test saving and loading sessions."""

    def test_save_session_creates_file(self, tmp_path):
        """save_session() should create a JSON file."""
        start_session()
        log_usage("groq/llama3-70b", 0.234, tokens_estimated=150)

        filename = str(tmp_path / "test_session.json")
        result = save_session(filename)

        assert Path(result).exists()
        with open(result) as f:
            data = json.load(f)

        assert "start_time" in data
        assert "model_calls" in data
        assert len(data["model_calls"]) == 1

    def test_load_session_restores_data(self, tmp_path):
        """load_session() should restore session data."""
        # Save a session
        start_session()
        log_usage("groq/llama3-70b", 0.234, tokens_estimated=150)
        filename = str(tmp_path / "test_session.json")
        save_session(filename)

        # Load it back
        loaded = load_session(filename)
        assert "model_calls" in loaded
        assert len(loaded["model_calls"]) == 1
        assert loaded["model_calls"][0]["model"] == "groq/llama3-70b"

    def test_save_session_auto_filename(self):
        """save_session() with no args should generate a filename."""
        start_session()
        log_usage("groq/llama3-70b", 0.234)
        filename = save_session()

        assert filename is not None
        assert "session_" in filename
        assert filename.endswith(".json")
        Path(filename).unlink()  # Cleanup


class TestEdgeCases:
    """Test boundary conditions and error handling."""

    def test_log_usage_before_session_starts(self):
        """log_usage() should handle being called before session start."""
        # Reset session state
        import timer
        timer._session_start = None

        log_usage("test/model", 0.1)
        # Should not crash; session should auto-start
        metrics = get_model_metrics("test/model")
        assert metrics["call_count"] >= 1

    def test_get_session_seconds_before_start(self):
        """get_session_seconds() before start should return 0."""
        import timer
        timer._session_start = None

        assert get_session_seconds() == 0.0

    def test_zero_and_negative_latencies(self):
        """Latencies at boundary values should work."""
        start_session()
        log_usage("test/model", 0.0)
        log_usage("test/model", 0.001)

        metrics = get_model_metrics("test/model")
        assert metrics["call_count"] == 2
        assert metrics["avg_latency_sec"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
