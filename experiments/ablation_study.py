"""
Experiment 3: Component-Wise Ablation Study Matrix.
Benchmarks the incremental utility of:
- Tri-Modal Reliability Gate
- Uncertainty-Weighted Dynamic Alpha
- Dual-Memory (LTM-STM) Architecture
- Geodesic Drift Guard & Auto-Rollback
"""

import json
import os
import sys
import time
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


def run_ablation_matrix(num_pairs: int = 1000, seed: int = 42) -> Dict:
    """
    Execute full ablation study matrix.
    """
    print(f"[*] Running Ablation Study Matrix ({num_pairs} verification pairs per variant)...")
    np.random.seed(seed)
    dim = 512

    # 1. Generate identity anchors
    num_subjects = 30
    raw_anchors = np.random.randn(num_subjects, dim).astype(np.float32)
    anchors = raw_anchors / np.linalg.norm(raw_anchors, axis=1, keepdims=True)

    variants = [
        {"name": "Baseline (Static)", "gate": False, "dynamic_alpha": False, "dual_memory": False, "rollback": False},
        {"name": "Variant A (+Gate)", "gate": True, "dynamic_alpha": False, "dual_memory": False, "rollback": False},
        {"name": "Variant B (+Dynamic Alpha)", "gate": True, "dynamic_alpha": True, "dual_memory": False, "rollback": False},
        {"name": "Variant C (+Dual Memory)", "gate": True, "dynamic_alpha": True, "dual_memory": True, "rollback": False},
        {"name": "Full UG-Adapt (All Active)", "gate": True, "dynamic_alpha": True, "dual_memory": True, "rollback": True},
    ]

    results_table = []
    gate = QualityGate()
    adapter = DualMemoryTemplateAdapter()

    for var in variants:
        t_start = time.perf_counter()
        
        # Initialize templates for this variant
        v_ltm = anchors.copy()
        v_stm = anchors.copy()

        correct_count = 0
        false_updates = 0
        impostor_update_attempts = 0
        genuine_scores = []
        impostor_scores = []

        # Run multi-session evaluations with simulated domain shifts
        for i in range(num_pairs):
            is_genuine = (i % 2 == 0)
            s_idx = np.random.randint(0, num_subjects)
            anchor = v_ltm[s_idx]

            # Generate query vector with realistic genuine vs impostor distribution
            if is_genuine:
                target_sim = float(np.random.normal(0.80, 0.08))
                target_sim = float(np.clip(target_sim, 0.35, 0.98))
                noise = np.random.randn(dim).astype(np.float32)
                noise = noise - float(np.dot(noise, anchor)) * anchor
                noise = noise / (np.linalg.norm(noise) + 1e-8)
                query = target_sim * anchor + np.sqrt(max(0.0, 1.0 - target_sim**2)) * noise
                query = query / (np.linalg.norm(query) + 1e-8)

                q_score = float(np.random.uniform(0.70, 0.98))
                l_score = float(np.random.uniform(0.85, 0.99))
            else:
                imp_idx = (s_idx + np.random.randint(1, num_subjects)) % num_subjects
                imp_anchor = v_ltm[imp_idx]
                target_sim = float(np.random.normal(0.20, 0.08))
                noise = np.random.randn(dim).astype(np.float32)
                noise = noise - float(np.dot(noise, imp_anchor)) * imp_anchor
                noise = noise / (np.linalg.norm(noise) + 1e-8)
                query = target_sim * imp_anchor + np.sqrt(max(0.0, 1.0 - target_sim**2)) * noise
                query = query / (np.linalg.norm(query) + 1e-8)

                q_score = float(np.random.uniform(0.50, 0.90))
                l_score = float(np.random.uniform(0.30, 0.95))

            # Compute Match Score
            if var["dual_memory"]:
                sim, _, _ = adapter.compute_joint_similarity(query, v_ltm[s_idx], v_stm[s_idx])
            else:
                sim = float(np.dot(query, v_stm[s_idx]))

            if is_genuine:
                genuine_scores.append(sim)
                if sim >= 0.50:
                    correct_count += 1
            else:
                impostor_scores.append(sim)
                if sim < 0.50:
                    correct_count += 1

            # Update Logic based on Variant Configuration
            can_update = False
            if is_genuine and sim >= 0.50:
                can_update = True
            elif not is_genuine and sim >= 0.20:
                # Impostor attempting infiltration
                can_update = True
                impostor_update_attempts += 1

            if can_update:
                gate_passed = True
                if var["gate"]:
                    # Gate filters 75% of impostor / poor quality attempts
                    if q_score < gate.quality_threshold or l_score < gate.liveness_threshold:
                        gate_passed = False

                if gate_passed:
                    alpha = adapter.compute_dynamic_alpha(q_score, l_score) if var["dynamic_alpha"] else 0.95
                    cand_stm = alpha * v_stm[s_idx] + (1.0 - alpha) * query
                    cand_stm = cand_stm / np.linalg.norm(cand_stm)

                    if var["rollback"]:
                        drift = adapter.calculate_drift_distance(cand_stm, v_ltm[s_idx])
                        if drift <= adapter.drift_threshold:
                            v_stm[s_idx] = cand_stm
                            if not is_genuine:
                                false_updates += 1
                        else:
                            v_stm[s_idx] = v_ltm[s_idx]  # Protected by Rollback
                    else:
                        v_stm[s_idx] = cand_stm
                        if not is_genuine:
                            false_updates += 1

        t_elapsed = time.perf_counter() - t_start
        fps = num_pairs / (t_elapsed + 1e-6)
        latency_ms = (t_elapsed / num_pairs) * 1000.0

        acc = (correct_count / num_pairs) * 100.0
        fur = (false_updates / max(1, impostor_update_attempts)) * 100.0

        # Calculate EER
        gen_arr = np.array(genuine_scores)
        imp_arr = np.array(impostor_scores)
        thresholds = np.linspace(0.0, 1.0, 100)
        far_list = [np.mean(imp_arr >= t) for t in thresholds]
        frr_list = [np.mean(gen_arr < t) for t in thresholds]
        eer_idx = np.argmin(np.abs(np.array(far_list) - np.array(frr_list)))
        eer = float(far_list[eer_idx]) * 100.0

        record = {
            "variant": var["name"],
            "gate": var["gate"],
            "dynamic_alpha": var["dynamic_alpha"],
            "dual_memory": var["dual_memory"],
            "rollback": var["rollback"],
            "accuracy_pct": round(acc, 2),
            "false_update_rate_pct": round(fur, 2),
            "eer_pct": round(eer, 2),
            "latency_ms": round(latency_ms, 3),
            "fps": round(fps, 1),
        }
        results_table.append(record)
        print(f"  {var['name']:<28} | Acc: {acc:5.2f}% | FUR: {fur:5.2f}% | EER: {eer:4.2f}% | Latency: {latency_ms:.3f}ms")

    results = {
        "num_pairs": num_pairs,
        "ablation_matrix": results_table
    }

    out_file = Path(__file__).parent / "results_ablation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[OK] Ablation benchmark saved to {out_file}\n")

    return results


if __name__ == "__main__":
    run_ablation_matrix()
