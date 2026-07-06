"""Basic sanity tests for all modules"""

import pytest


class TestModuleImports:
    """Verify all modules can be imported"""

    def test_speclab_import(self):
        from speclab.runner import run_speclab
        assert callable(run_speclab)

    def test_sentinelbench_import(self):
        from sentinelbench.runner import run_sentinelbench
        assert callable(run_sentinelbench)

    def test_skillforge_import(self):
        from skillforge.runner import run_skillforge
        assert callable(run_skillforge)

    def test_portfolio_analyzer_import(self):
        from notebooks.portfolio_analyzer.analyzer import PortfolioAnalyzer
        analyzer = PortfolioAnalyzer()
        assert hasattr(analyzer, 'generate_portfolio_report')

    def test_orchestrator_import(self):
        from compare.orchestrator import ResearchOrchestrator
        orch = ResearchOrchestrator()
        assert hasattr(orch, 'run_all_projects')

    def test_comparator_import(self):
        from compare.interactive_compare.comparator import InteractiveComparator
        comp = InteractiveComparator()
        assert hasattr(comp, 'generate_comparison_dashboard_data')


class TestCliEntry:
    """Verify CLI entry point works"""

    def test_main_help(self):
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--help"],
            cwd=".",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0

    def test_main_status(self):
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "status"],
            cwd=".",
            capture_output=True,
            text=True,
            timeout=10
        )
        # Status should complete (even if offline)
        assert result.returncode in [0, 1]  # OK or graceful error


class TestSampleResults:
    """Verify sample results are valid"""

    def test_speclab_results_valid(self):
        import json
        from pathlib import Path

        f = Path("speclab/results/run_2026_09_15.json")
        if f.exists():
            with open(f) as fp:
                data = json.load(fp)
                assert data["project"] == "speclab"
                assert "scenarios" in data

    def test_sentinelbench_results_valid(self):
        import json
        from pathlib import Path

        f = Path("sentinelbench/results/run_2026_09_15.json")
        if f.exists():
            with open(f) as fp:
                data = json.load(fp)
                assert data["project"] == "sentinelbench"
                assert "transcripts" in data

    def test_skillforge_results_valid(self):
        import json
        from pathlib import Path

        f = Path("skillforge/results/run_2026_09_15.json")
        if f.exists():
            with open(f) as fp:
                data = json.load(fp)
                assert data["project"] == "skillforge"
                assert "ai_assisted_scores" in data or "summary" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
