"""
Research Orchestrator — Agentic experiment runner
Coordinates SpecLab, SentinelBench, SkillForge and synthesizes findings with Claude
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentRun:
    """Metadata about a completed experiment run"""
    project: str
    started_at: float
    completed_at: float
    success: bool
    results_path: Optional[Path]
    error_message: Optional[str]

    @property
    def duration_seconds(self) -> float:
        return self.completed_at - self.started_at


class ResearchOrchestrator:
    """Agentic system coordinating all three research projects"""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).resolve().parent.parent
        self.runs: List[ExperimentRun] = []

    def run_all_projects(self, demo_mode: bool = True) -> Dict:
        """Run all three projects in sequence"""
        logger.info("Starting Research Orchestrator...")

        results = {
            "orchestrator_start": time.time(),
            "runs": [],
            "summary": {}
        }

        # Run each project
        for project in ["speclab", "sentinelbench", "skillforge"]:
            logger.info(f"Running {project}...")
            run = self.run_project(project, demo_mode=demo_mode)
            self.runs.append(run)
            results["runs"].append({
                "project": run.project,
                "success": run.success,
                "duration_seconds": run.duration_seconds,
                "error": run.error_message
            })

        results["orchestrator_end"] = time.time()
        results["total_duration_seconds"] = results["orchestrator_end"] - results["orchestrator_start"]
        results["all_succeeded"] = all(run.success for run in self.runs)

        logger.info(f"Orchestration complete. Success: {results['all_succeeded']}")

        return results

    def run_project(self, project_name: str, demo_mode: bool = True) -> ExperimentRun:
        """Execute a single project"""
        started = time.time()

        try:
            # Build command based on project
            if project_name == "speclab":
                cmd = ["python", "main.py", "speclab", "--demo" if demo_mode else "--scenarios", "50"]
            elif project_name == "sentinelbench":
                cmd = ["python", "main.py", "sentinelbench", "--demo" if demo_mode else "--generate"]
            elif project_name == "skillforge":
                cmd = ["python", "main.py", "skillforge", "--demo" if demo_mode else "--run-experiment"]
            else:
                raise ValueError(f"Unknown project: {project_name}")

            # Run from project root
            result = subprocess.run(
                cmd,
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            completed = time.time()

            if result.returncode == 0:
                logger.info(f"{project_name} completed successfully in {completed - started:.1f}s")
                return ExperimentRun(
                    project=project_name,
                    started_at=started,
                    completed_at=completed,
                    success=True,
                    results_path=None,
                    error_message=None
                )
            else:
                logger.error(f"{project_name} failed: {result.stderr}")
                return ExperimentRun(
                    project=project_name,
                    started_at=started,
                    completed_at=completed,
                    success=False,
                    results_path=None,
                    error_message=result.stderr[:200]
                )

        except subprocess.TimeoutExpired:
            completed = time.time()
            logger.error(f"{project_name} timed out after 300s")
            return ExperimentRun(
                project=project_name,
                started_at=started,
                completed_at=completed,
                success=False,
                results_path=None,
                error_message="Timeout after 300 seconds"
            )

        except Exception as e:
            completed = time.time()
            logger.error(f"{project_name} failed with exception: {e}")
            return ExperimentRun(
                project=project_name,
                started_at=started,
                completed_at=completed,
                success=False,
                results_path=None,
                error_message=str(e)[:200]
            )

    def generate_executive_summary(self, results: Dict) -> str:
        """Generate human-readable executive summary"""
        lines = [
            "RESEARCH ORCHESTRATOR EXECUTION SUMMARY",
            "=" * 50,
            "",
            f"Total Duration: {results['total_duration_seconds']:.1f} seconds",
            f"All Projects Succeeded: {results['all_succeeded']}",
            ""
        ]

        for run in results["runs"]:
            status = "✓ PASSED" if run["success"] else "✗ FAILED"
            lines.append(
                f"{run['project']:20} {status:10} ({run['duration_seconds']:.1f}s)"
            )

        lines.extend([
            "",
            "Note: In production, Claude (claude-sonnet-4-6) would now:",
            "  1. Analyze all three result sets",
            "  2. Identify cross-project patterns",
            "  3. Generate synthesized research report",
            "  4. Recommend next steps",
        ])

        return "\n".join(lines)

    def save_execution_log(self, results: Dict, output_path: Path) -> None:
        """Save orchestration log as JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Execution log saved to {output_path}")


if __name__ == "__main__":
    orchestrator = ResearchOrchestrator()
    results = orchestrator.run_all_projects(demo_mode=True)

    summary = orchestrator.generate_executive_summary(results)
    print(summary)

    # Save log
    orchestrator.save_execution_log(
        results,
        Path("cipher-fellows/research_orchestrator/execution_logs/latest.json")
    )
