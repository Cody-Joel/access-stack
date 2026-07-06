"""chart_findings.py — turn an analyze_batch CSV into figures for your writeup.

First: python analyze_batch.py --csv summary.csv
Then:  python chart_findings.py summary.csv
Needs matplotlib:  pip install matplotlib

Produces:
  agreement_by_condition.png  — the headline: do models agree more with explanations?
  lean_by_condition.png       — which value each condition leans toward
"""

import csv
import sys
from collections import defaultdict, Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "summary.csv"
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("No rows in CSV. Run analyze_batch.py --csv summary.csv first.")
        return

    # ---- Agreement by condition ----
    by_sc = defaultdict(list)
    for r in rows:
        by_sc[(r["scenario_id"], r["condition"])].append(r)

    cond_scores = defaultdict(list)
    for (_sid, cond), group in by_sc.items():
        per_model = defaultdict(list)
        for r in group:
            per_model[r["model"]].append(r["lean"])
        model_lean = {m: Counter(v).most_common(1)[0][0] for m, v in per_model.items()}
        if model_lean:
            majority = Counter(model_lean.values()).most_common(1)[0][1]
            cond_scores[cond].append(majority / len(model_lean))

    conds = sorted(cond_scores)
    means = [sum(cond_scores[c]) / len(cond_scores[c]) * 100 for c in conds]

    plt.figure(figsize=(5, 4))
    plt.bar(conds, means, color=["#7c3aed", "#22d3a5", "#4f8ef7", "#f59e0b"][:len(conds)])
    plt.ylabel("Mean cross-model agreement (%)")
    plt.title("Model agreement by spec condition")
    plt.ylim(0, 100)
    for i, v in enumerate(means):
        plt.text(i, v + 1, f"{v:.0f}%", ha="center")
    plt.tight_layout()
    plt.savefig("agreement_by_condition.png", dpi=150)
    print("saved agreement_by_condition.png")

    # ---- Value lean distribution by condition ----
    leans = sorted({r["lean"] for r in rows})
    conds2 = sorted({r["condition"] for r in rows})
    counts = {c: Counter(r["lean"] for r in rows if r["condition"] == c) for c in conds2}

    width = 0.8 / max(1, len(conds2))
    plt.figure(figsize=(7, 4))
    for j, c in enumerate(conds2):
        total = sum(counts[c].values()) or 1
        vals = [counts[c].get(l, 0) / total * 100 for l in leans]
        offsets = [i + j * width for i in range(len(leans))]
        plt.bar(offsets, vals, width=width, label=c)
    plt.xticks([i + width * (len(conds2) - 1) / 2 for i in range(len(leans))],
               leans, rotation=30, ha="right")
    plt.ylabel("% of responses")
    plt.title("Value lean by condition")
    plt.legend()
    plt.tight_layout()
    plt.savefig("lean_by_condition.png", dpi=150)
    print("saved lean_by_condition.png")


if __name__ == "__main__":
    main()
