"""
Experiment 1: Longitudinal Recognition Accuracy Benchmark across 30 Days.
Simulates natural face variation (lighting, accessories, hairstyles, pose) over time.
Compares Static Baseline vs. Naive EMA vs. Proposed UG-Adapt.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Add project root to sys.path
BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from auto_attendance.quality_gate import QualityGate
from auto_attendance.template_adapter import DualMemoryTemplateAdapter


def generate_synthetic_identities(num_subjects: int = 50, dim: int = 512, seed: int = 42) -> np.ndarray:
    """Generate ground truth identity embeddings on the unit hypersphere."""
    np.random.seed(seed)
    embeddings = np.random.randn(num_subjects, dim).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms


def simulate_session_sample(
    anchor_vector: np.ndarray,
    current_identity_vector: np.ndarray,
    day: int,
) -> Tuple[np.ndarray, float, float]:
    """
    Simulate an operational live observation vector on day t with natural drift and quality variations.
    """
    dim = len(anchor_vector)
    # Target similarity to current ground truth
    target_sim = float(np.random.normal(0.78, 0.08))
    target_sim = float(np.clip(target_sim, 0.35, 0.96))

    noise = np.random.randn(dim).astype(np.float32)
    noise = noise - float(np.dot(noise, current_identity_vector)) * current_identity_vector
    noise = noise / (np.linalg.norm(noise) + 1e-8)

    live_vec = target_sim * current_identity_vector + np.sqrt(max(0.0, 1.0 - target_sim**2)) * noise
    live_vec = live_vec / (np.linalg.norm(live_vec) + 1e-8)

    # Realistic quality distribution (85% high quality, 15% difficult)
    if np.random.rand() < 0.15:
        base_q = float(np.random.uniform(0.45, 0.62))  # Challenging frame
    else:
        base_q = float(np.random.uniform(0.72, 0.98))  # Good frame

    # Liveness distribution
    if np.random.rand() < 0.04:
        liveness_score = float(np.random.uniform(0.20, 0.50))
    else:
        liveness_score = float(np.random.uniform(0.86, 0.99))

    return live_vec, base_q, liveness_score


def run_longitudinal_benchmark(
    num_subjects: int = 50,
    num_days: int = 30,
    samples_per_day: int = 10,
    seed: int = 42
) -> Dict:
    """
    Execute 30-day longitudinal attendance benchmark.
    """
    print(f"[*] Running Longitudinal Benchmark ({num_subjects} subjects, {num_days} days, {samples_per_day} samples/day)...")
    np.random.seed(seed)
    dim = 512
    
    anchors = generate_synthetic_identities(num_subjects, dim=dim, seed=seed)
    subject_evolution = anchors.copy()

    static_templates = anchors.copy()
    naive_templates = anchors.copy()
    ug_ltm = anchors.copy()
    ug_stm = anchors.copy()
    
    gate = QualityGate()
    adapter = DualMemoryTemplateAdapter(alpha_base=0.90, drift_threshold=0.35, dual_lambda=0.60)
    
    threshold = 0.54  # Strict operational threshold
    
    history_static: List[float] = []
    history_naive: List[float] = []
    history_ug_adapt: List[float] = []

    for day in range(1, num_days + 1):
        correct_static = 0
        correct_naive = 0
        correct_ug = 0
        total_evals = num_subjects * samples_per_day

        # Update real-world appearance slightly each day
        for s in range(num_subjects):
            day_shift = np.random.randn(dim).astype(np.float32) * 0.0075
            subject_evolution[s] = subject_evolution[s] + day_shift
            subject_evolution[s] = subject_evolution[s] / np.linalg.norm(subject_evolution[s])

        for s_idx in range(num_subjects):
            current_face = subject_evolution[s_idx]

            for _ in range(samples_per_day):
                live_emb, q_score, l_score = simulate_session_sample(anchors[s_idx], current_face, day)

                # ==========================================
                # 1. Evaluate Static Model
                # ==========================================
                sim_static = float(np.dot(live_emb, static_templates[s_idx]))
                if sim_static >= threshold:
                    correct_static += 1

                # ==========================================
                # 2. Evaluate Naive EMA Model
                # ==========================================
                sim_naive = float(np.dot(live_emb, naive_templates[s_idx]))
                if sim_naive >= threshold:
                    correct_naive += 1
                
                # Naive EMA blindly updates on all recognized frames (even low quality / spoof)
                if sim_naive >= 0.40:
                    cand_naive = 0.95 * naive_templates[s_idx] + 0.05 * live_emb
                    naive_templates[s_idx] = cand_naive / np.linalg.norm(cand_naive)

                # ==========================================
                # 3. Evaluate Proposed UG-Adapt
                # ==========================================
                joint_sim, _, _ = adapter.compute_joint_similarity(
                    live_embedding=live_emb,
                    ltm_anchor=ug_ltm[s_idx],
                    stm_prototype=ug_stm[s_idx]
                )
                if joint_sim >= threshold:
                    correct_ug += 1

                # Gate check for safe adaptation
                if q_score >= gate.quality_threshold and l_score >= gate.liveness_threshold:
                    new_stm, status, _metrics = adapter.adapt(
                        live_embedding=live_emb,
                        ltm_anchor=ug_ltm[s_idx],
                        current_stm=ug_stm[s_idx],
                        quality_score=q_score,
                        liveness_score=l_score
                    )
                    ug_stm[s_idx] = new_stm

        acc_static = (correct_static / total_evals) * 100.0
        acc_naive = (correct_naive / total_evals) * 100.0
        acc_ug = (correct_ug / total_evals) * 100.0

        history_static.append(round(acc_static, 2))
        history_naive.append(round(acc_naive, 2))
        history_ug_adapt.append(round(acc_ug, 2))

        if day % 5 == 0 or day == 1 or day == num_days:
            print(f"  Day {day:02d} | Static: {acc_static:5.2f}% | Naive EMA: {acc_naive:5.2f}% | UG-Adapt: {acc_ug:5.2f}%")

    results = {
        "num_days": num_days,
        "num_subjects": num_subjects,
        "days": list(range(1, num_days + 1)),
        "accuracy_static": history_static,
        "accuracy_naive_ema": history_naive,
        "accuracy_ug_adapt": history_ug_adapt,
        "summary": {
            "day_1": {
                "static": history_static[0],
                "naive": history_naive[0],
                "ug_adapt": history_ug_adapt[0]
            },
            "day_10": {
                "static": history_static[9],
                "naive": history_naive[9],
                "ug_adapt": history_ug_adapt[9]
            },
            "day_20": {
                "static": history_static[19],
                "naive": history_naive[19],
                "ug_adapt": history_ug_adapt[19]
            },
            "day_30": {
                "static": history_static[-1],
                "naive": history_naive[-1],
                "ug_adapt": history_ug_adapt[-1]
            },
        }
    }

    out_file = Path(__file__).parent / "results_longitudinal.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[OK] Longitudinal benchmark saved to {out_file}\n")

    return results


if __name__ == "__main__":
    run_longitudinal_benchmark()
