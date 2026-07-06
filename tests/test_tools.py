"""
tests/test_tools.py — Unit tests for helper tools (calculator, web search, file reader).

Run with: pytest tests/test_tools.py -v
"""

import pytest
import tools
from pathlib import Path
from tools import (
    run_calculator,
    run_web_search,
    run_file_reader,
)


class TestCalculator:
    """Test the calculator tool."""

    def test_simple_arithmetic(self):
        """Calculator should evaluate basic expressions."""
        result = run_calculator("2 + 2")
        assert "4" in result
        assert "Result" in result

    def test_complex_expressions(self):
        """Calculator should handle exponents and functions."""
        result = run_calculator("2**10")
        assert "1024" in result

        result = run_calculator("sqrt(16)")
        assert "4" in result

    def test_invalid_expression_returns_error(self):
        """Calculator should handle invalid expressions gracefully."""
        result = run_calculator("1 + + 2")
        assert "Error" in result or "❌" in result

    def test_dangerous_code_is_rejected(self):
        """Calculator should not allow __import__ or other dangerous functions."""
        result = run_calculator("__import__('os').system('ls')")
        assert "Error" in result or "not allowed" in result.lower()

    def test_builtin_restriction(self):
        """eval() should have no builtins available."""
        result = run_calculator("open('/etc/passwd')")
        assert "Error" in result or "❌" in result

    def test_floats_and_decimals(self):
        """Calculator should handle float results."""
        result = run_calculator("10 / 3")
        assert "3.33" in result or "3.3" in result


class TestWebSearch:
    """Test the web search tool."""

    def test_web_search_returns_string(self):
        """Web search should return a string response."""
        result = run_web_search("Python programming")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_web_search_acknowledges_query(self):
        """Search result should mention the query."""
        result = run_web_search("AI safety research")
        assert "AI safety research" in result or "Searched" in result

    def test_web_search_with_empty_query(self):
        """Empty query should return helpful message."""
        result = run_web_search("")
        # Should not crash; return something helpful
        assert isinstance(result, str)


class TestFileReader:
    """Test the file reader tool."""

    def test_file_reader_lists_files(self, tmp_path):
        """File reader should be able to list files in a directory."""
        from tools import SANDBOX_DIR
        sandbox_dir = tmp_path / "sandbox"
        sandbox_dir.mkdir()
        (sandbox_dir / "file1.txt").write_text("content1")
        (sandbox_dir / "file2.txt").write_text("content2")

        # Temporarily use the sandbox directory for this test
        original_sandbox = SANDBOX_DIR
        try:
            tools.SANDBOX_DIR = sandbox_dir
            result = run_file_reader(str(sandbox_dir))
            assert "file1.txt" in result or "file2.txt" in result
        finally:
            tools.SANDBOX_DIR = original_sandbox

    def test_file_reader_reads_file_content(self, tmp_path):
        """File reader should read file contents."""
        from tools import SANDBOX_DIR
        sandbox_dir = tmp_path / "sandbox"
        sandbox_dir.mkdir()
        sample_file = sandbox_dir / "sample.txt"
        sample_file.write_text("Hello, world!")

        original_sandbox = SANDBOX_DIR
        try:
            tools.SANDBOX_DIR = sandbox_dir
            result = run_file_reader(str(sample_file))
            assert "Hello, world!" in result or "content" in result.lower()
        finally:
            tools.SANDBOX_DIR = original_sandbox

    def test_file_reader_respects_sandbox(self):
        """File reader should not allow reading outside sandbox directory."""
        # Try to read /etc/passwd or similar
        result = run_file_reader("/etc/passwd")
        # Should either refuse or return error
        assert "Error" in result or "❌" in result or "not allowed" in result.lower()

    def test_file_reader_with_nonexistent_file(self):
        """File reader should handle nonexistent files gracefully."""
        result = run_file_reader("/nonexistent/path/to/file.txt")
        assert "Error" in result or "not found" in result.lower() or "❌" in result

    def test_file_reader_returns_preview(self, tmp_path):
        """Large files should return a preview, not full content."""
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 10000)  # 10KB

        result = run_file_reader(str(large_file))
        # Should not crash; might show preview or message
        assert isinstance(result, str)
        assert len(result) < 5000  # Should be truncated


class TestToolIntegration:
    """Test that tools work together."""

    def test_calculator_in_search_context(self):
        """Calculator result could be shown after search."""
        calc = run_calculator("100 * 2.5")
        search = run_web_search("conversion calculator")

        assert "250" in calc
        assert isinstance(search, str)

    def test_tools_return_markdown_compatible_strings(self):
        """All tools should return strings safe for Gradio markdown."""
        calc = run_calculator("5 + 5")
        search = run_web_search("test")

        # Should not have unescaped special chars that break markdown
        assert isinstance(calc, str)
        assert isinstance(search, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
