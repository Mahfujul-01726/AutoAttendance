"""
Master Experiment Runner for UG-Adapt Research Framework.
Executes all benchmark experiments, compiles metrics, prints LaTeX tables, and creates figures.

Usage:
    python experiments/run_all_experiments.py
"""

import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from experiments.ablation_study import run_ablation_matrix
from experiments.evaluate_longitudinal import run_longitudinal_benchmark
from experiments.evaluate_poisoning import run_poisoning_benchmark
from experiments.generate_plots import generate_all_plots


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  [*] {title}")
    print("=" * 70)


def print_latex_tables():
    """Print publication-ready LaTeX tables generated from the results."""
    long_file = Path(__file__).parent / "results_longitudinal.json"
    ablation_file = Path(__file__).parent / "results_ablation.json"
    poison_file = Path(__file__).parent / "results_poisoning.json"

    print_banner("LATEX CODE FOR RESEARCH PAPER / THESIS REPORT")

    if long_file.exists() and ablation_file.exists():
        with open(long_file, "r") as f:
            long_data = json.load(f)
        with open(ablation_file, "r") as f:
            ab_data = json.load(f)

        s = long_data["summary"]

        print("% TABLE 1: Longitudinal Accuracy Comparison across 30 Days")
        print(r"""\begin{table}[htbp]
\centering
\caption{Longitudinal Recognition Accuracy (\%) across 30 Operational Days}
\label{tab:longitudinal_acc}
\begin{tabular}{lcccc}
\hline
\textbf{Model / Pipeline} & \textbf{Day 1} & \textbf{Day 10} & \textbf{Day 20} & \textbf{Day 30} \\
\hline""")
        print(f"InsightFace (Static Baseline) & {s['day_1']['static']:.2f}\\% & {s['day_10']['static']:.2f}\\% & {s['day_20']['static']:.2f}\\% & {s['day_30']['static']:.2f}\\% \\\\")
        print(f"InsightFace + Naive EMA & {s['day_1']['naive']:.2f}\\% & {s['day_10']['naive']:.2f}\\% & {s['day_20']['naive']:.2f}\\% & {s['day_30']['naive']:.2f}\\% (Drifted) \\\\")
        print(f"\\textbf{{Proposed UG-Adapt}} & \\textbf{{{s['day_1']['ug_adapt']:.2f}\\%}} & \\textbf{{{s['day_10']['ug_adapt']:.2f}\\%}} & \\textbf{{{s['day_20']['ug_adapt']:.2f}\\%}} & \\textbf{{{s['day_30']['ug_adapt']:.2f}\\%}} \\\\")
        print(r"""\hline
\end{tabular}
\end{table}
""")

        print("% TABLE 2: Component-wise Ablation Study Matrix")
        print(r"""\begin{table}[htbp]
\centering
\caption{Ablation Study of Proposed UG-Adapt Framework Components}
\label{tab:ablation_study}
\begin{tabular}{lcccccc}
\hline
\textbf{Configuration} & \textbf{Gate} & \textbf{$\alpha(t)$} & \textbf{Dual-Mem} & \textbf{Rollback} & \textbf{Acc (\%)} & \textbf{FUR (\%)} \\
\hline""")
        for row in ab_data["ablation_matrix"]:
            g = r"\checkmark" if row["gate"] else r"\texttimes"
            a = r"\checkmark" if row["dynamic_alpha"] else r"\texttimes"
            d = r"\checkmark" if row["dual_memory"] else r"\texttimes"
            r_mark = r"\checkmark" if row["rollback"] else r"\texttimes"
            name = row["variant"]
            acc = f"{row['accuracy_pct']:.2f}\\%"
            fur = f"{row['false_update_rate_pct']:.2f}\\%"
            if "Full UG-Adapt" in name:
                print(f"\\textbf{{{name}}} & {g} & {a} & {d} & {r_mark} & \\textbf{{{acc}}} & \\textbf{{{fur}}} \\\\")
            else:
                print(f"{name} & {g} & {a} & {d} & {r_mark} & {acc} & {fur} \\\\")
        print(r"""\hline
\end{tabular}
\end{table}
""")


def main():
    start_time = time.time()
    print_banner("STARTING COMPLETE UG-ADAPT RESEARCH BENCHMARK SUITE")

    # 1. Run Longitudinal Benchmark (30 Days)
    run_longitudinal_benchmark(num_subjects=50, num_days=30, samples_per_day=10)

    # 2. Run Poisoning & Presentation Attack Benchmark (500 trials)
    run_poisoning_benchmark(num_trials=500)

    # 3. Run Component Ablation Study Matrix (1,000 pairs)
    run_ablation_matrix(num_pairs=1000)

    # 4. Generate 4 High-Resolution Vector Figures in paper/figures/
    generate_all_plots()

    # 5. Print LaTeX Tables
    print_latex_tables()

    elapsed = time.time() - start_time
    print_banner(f"ALL BENCHMARKS & PLOTS COMPLETED IN {elapsed:.2f} SECONDS!")
    print("📁 Results saved in: experiments/ (JSON) and paper/figures/ (PNG/Plots)")


if __name__ == "__main__":
    main()
