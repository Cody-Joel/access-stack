"""
Interactive Comparator — Side-by-side analysis of model behaviors
Shows how models differ on spec conflicts, monitor evasion, and learning efficiency
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics


@dataclass
class ModelComparison:
    """Comparison of model performance on a single dimension"""
    dimension: str  # e.g., "honesty_vs_helpfulness"
    models: Dict[str, float]  # model_name -> score
    winner: str  # model with highest score
    margin: float  # percentage point difference


class InteractiveComparator:
    """Compare models across all three research projects"""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).resolve().parent.parent

    def load_speclab_by_model(self) -> Dict[str, Dict[str, List[float]]]:
        """Load SpecLab divergence scores grouped by model and category."""
        results_dir = self.base_path / "speclab" / "results"
        by_model = {}

        if results_dir.exists():
            for json_file in results_dir.glob("*.json"):
                with open(json_file) as f:
                    data = json.load(f)
                    for scenario in data.get("scenarios", []):
                        model = scenario.get("model", "unknown")
                        divergence = scenario.get("divergence_score", 0)
                        category = scenario.get("conflict_type", "unknown")
                        by_model.setdefault(model, {}).setdefault(category, []).append(divergence)

        return by_model

    def load_sentinelbench_by_model(self) -> Dict[str, List[float]]:
        """Load SentinelBench blind spot miss rates grouped by model"""
        results_dir = self.base_path / "sentinelbench" / "results"
        by_model = {}

        if results_dir.exists():
            for json_file in results_dir.glob("*.json"):
                with open(json_file) as f:
                    data = json.load(f)
                    for transcript in data.get("transcripts", []):
                        model = transcript.get("monitor_model", "claude")
                        missed = transcript.get("missed", 0)
                        if model not in by_model:
                            by_model[model] = []
                        by_model[model].append(float(missed))

        return by_model

    def load_skillforge_by_condition(self) -> Dict[str, Dict[str, List[float]]]:
        """Load SkillForge scores grouped by AI-assisted vs solo"""
        results_dir = self.base_path / "skillforge" / "results"
        by_condition = {"ai_assisted": {}, "solo": {}}

        if results_dir.exists():
            for json_file in results_dir.glob("*.json"):
                with open(json_file) as f:
                    data = json.load(f)

                    # AI-assisted scores
                    for entry in data.get("ai_assisted", []):
                        task = entry.get("task_id", "default")
                        score = entry.get("final_score", 0)
                        if task not in by_condition["ai_assisted"]:
                            by_condition["ai_assisted"][task] = []
                        by_condition["ai_assisted"][task].append(score)

                    # Solo scores
                    for entry in data.get("solo", []):
                        task = entry.get("task_id", "default")
                        score = entry.get("final_score", 0)
                        if task not in by_condition["solo"]:
                            by_condition["solo"][task] = []
                        by_condition["solo"][task].append(score)

        return by_condition

    def compare_speclab_models(self) -> List[ModelComparison]:
        """Compare models on value-conflict consistency (lower divergence is better)"""
        by_model = self.load_speclab_by_model()
        comparisons = []

        if len(by_model) < 2:
            return comparisons

        categories = set()
        for model_data in by_model.values():
            categories.update(model_data.keys())

        for category in sorted(categories):
            scores = {
                model: statistics.mean(model_data.get(category, []))
                for model, model_data in by_model.items()
                if model_data.get(category)
            }

            if len(scores) < 2:
                continue

            sorted_scores = sorted(scores.items(), key=lambda x: x[1])
            winner = sorted_scores[0][0]
            margin = sorted_scores[-1][1] - sorted_scores[0][1]

            comparisons.append(ModelComparison(
                dimension=f"speclab_{category}",
                models=scores,
                winner=winner,
                margin=margin
            ))

        return comparisons

    def compare_sentinelbench_models(self) -> List[ModelComparison]:
        """Compare monitor models on blind spot detection (lower miss rate is better)"""
        by_model = self.load_sentinelbench_by_model()
        comparisons = []

        if len(by_model) < 2:
            return comparisons

        # Lower miss rate = better (catches more blind spots)
        scores = {
            model: statistics.mean(missed)
            for model, missed in by_model.items()
            if missed
        }

        if len(scores) >= 2:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1])
            winner = sorted_scores[0][0]
            margin = sorted_scores[-1][1] - sorted_scores[0][1]

            comparisons.append(ModelComparison(
                dimension="sentinelbench_blind_spot_miss_rate",
                models=scores,
                winner=winner,
                margin=margin
            ))

        return comparisons

    def compare_skillforge_conditions(self) -> Dict[str, any]:
        """Compare AI-assisted vs solo learning outcomes"""
        by_condition = self.load_skillforge_by_condition()

        ai_scores = []
        solo_scores = []

        for task_scores in by_condition["ai_assisted"].values():
            ai_scores.extend(task_scores)

        for task_scores in by_condition["solo"].values():
            solo_scores.extend(task_scores)

        if not (ai_scores and solo_scores):
            return {}

        ai_avg = statistics.mean(ai_scores)
        solo_avg = statistics.mean(solo_scores)

        return {
            "ai_assisted_avg": ai_avg,
            "solo_avg": solo_avg,
            "gap_percentage": ((solo_avg - ai_avg) / solo_avg) * 100 if solo_avg > 0 else 0,
            "ai_variance": statistics.variance(ai_scores) if len(ai_scores) > 1 else 0,
            "solo_variance": statistics.variance(solo_scores) if len(solo_scores) > 1 else 0,
        }

    def generate_comparison_dashboard_data(self) -> Dict:
        """Generate all comparison data for dashboard visualization"""
        return {
            "speclab_comparisons": [
                {
                    "dimension": c.dimension,
                    "models": c.models,
                    "winner": c.winner,
                    "margin": f"{c.margin:.2%}"
                }
                for c in self.compare_speclab_models()
            ],
            "sentinelbench_comparisons": [
                {
                    "dimension": c.dimension,
                    "models": c.models,
                    "winner": c.winner,
                    "margin": f"{c.margin:.2%}"
                }
                for c in self.compare_sentinelbench_models()
            ],
            "skillforge_analysis": self.compare_skillforge_conditions()
        }

    def export_comparison_html(self, output_path: Path) -> None:
        """Export interactive comparison as HTML for portfolio"""
        data = self.generate_comparison_dashboard_data()

        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Model Comparison Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 20px; }
        .comparison { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
        .metric { margin: 10px 0; }
        .winner { color: #2ecc71; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <h1>Cipher-Fellows Model Comparison</h1>
"""

        if data.get("speclab_comparisons"):
            html += "<h2>SpecLab: Value Conflict Consistency</h2>"
            for comp in data["speclab_comparisons"]:
                html += f"""
    <div class="comparison">
        <h3>{comp['dimension']}</h3>
        <table>
            <tr><th>Model</th><th>Score</th></tr>
"""
                for model, score in sorted(comp["models"].items(), key=lambda x: x[1]):
                    highlight = ' class="winner"' if model == comp["winner"] else ""
                    html += f"            <tr><td{highlight}>{model}</td><td{highlight}>{score:.2%}</td></tr>\n"
                html += f"""
        </table>
        <p>Winner: <span class="winner">{comp['winner']}</span> (margin: {comp['margin']})</p>
    </div>
"""

        if data.get("sentinelbench_comparisons"):
            html += "<h2>SentinelBench: Monitor Blind Spot Detection</h2>"
            for comp in data["sentinelbench_comparisons"]:
                html += f"""
    <div class="comparison">
        <h3>{comp['dimension']}</h3>
        <table>
            <tr><th>Model</th><th>Miss Rate</th></tr>
"""
                for model, score in sorted(comp["models"].items(), key=lambda x: x[1]):
                    highlight = ' class="winner"' if model == comp["winner"] else ""
                    html += f"            <tr><td{highlight}>{model}</td><td{highlight}>{score:.2%}</td></tr>\n"
                html += f"""
        </table>
        <p>Best Detector: <span class="winner">{comp['winner']}</span></p>
    </div>
"""

        if data.get("skillforge_analysis"):
            html += "<h2>SkillForge: Learning Efficiency</h2>"
            sf = data["skillforge_analysis"]
            if sf:
                html += f"""
    <div class="comparison">
        <div class="metric">
            <strong>AI-Assisted Average:</strong> {sf.get('ai_assisted_avg', 0):.1%}
        </div>
        <div class="metric">
            <strong>Solo Average:</strong> {sf.get('solo_avg', 0):.1%}
        </div>
        <div class="metric">
            <strong>Mastery Gap:</strong> <span class="winner">{sf.get('gap_percentage', 0):.1f}%</span>
        </div>
    </div>
"""

        html += """
</body>
</html>
"""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)


if __name__ == "__main__":
    comp = InteractiveComparator()
    data = comp.generate_comparison_dashboard_data()
    print(json.dumps(data, indent=2))

    comp.export_comparison_html(Path("docs/comparison.html"))
